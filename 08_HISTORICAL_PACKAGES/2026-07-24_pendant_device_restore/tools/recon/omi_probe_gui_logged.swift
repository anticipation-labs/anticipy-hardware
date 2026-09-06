import AppKit
import CoreBluetooth
import CryptoKit
import Darwin
import Foundation

private let audioServiceUUID = CBUUID(string: "19B10000-E8F2-537E-4F6C-D104768A1214")
private let audioDataUUID = CBUUID(string: "19B10001-E8F2-537E-4F6C-D104768A1214")
private let codecUUID = CBUUID(string: "19B10002-E8F2-537E-4F6C-D104768A1214")
private let batteryServiceUUID = CBUUID(string: "180F")
private let batteryLevelUUID = CBUUID(string: "2A19")

setbuf(stdout, nil)

private func sha256Hex(_ data: Data) -> String {
  SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

private func authorizationName(_ authorization: CBManagerAuthorization) -> String {
  switch authorization {
  case .allowedAlways: return "allowed_always"
  case .denied: return "denied"
  case .restricted: return "restricted"
  case .notDetermined: return "not_determined"
  @unknown default: return "unknown"
  }
}

private func stateName(_ state: CBManagerState) -> String {
  switch state {
  case .poweredOn: return "powered_on"
  case .poweredOff: return "powered_off"
  case .resetting: return "resetting"
  case .unauthorized: return "unauthorized"
  case .unsupported: return "unsupported"
  case .unknown: return "unknown"
  @unknown default: return "unknown_future"
  }
}

private func propertyNames(_ properties: CBCharacteristicProperties) -> [String] {
  var names: [String] = []
  if properties.contains(.broadcast) { names.append("broadcast") }
  if properties.contains(.read) { names.append("read") }
  if properties.contains(.writeWithoutResponse) { names.append("write_without_response") }
  if properties.contains(.write) { names.append("write") }
  if properties.contains(.notify) { names.append("notify") }
  if properties.contains(.indicate) { names.append("indicate") }
  if properties.contains(.authenticatedSignedWrites) { names.append("authenticated_signed_writes") }
  if properties.contains(.extendedProperties) { names.append("extended_properties") }
  if properties.contains(.notifyEncryptionRequired) { names.append("notify_encryption_required") }
  if properties.contains(.indicateEncryptionRequired) { names.append("indicate_encryption_required") }
  return names
}

private final class FrameMetrics {
  private(set) var sequenceGaps = 0
  private(set) var duplicatePackets = 0
  private(set) var malformedPackets = 0
  private(set) var droppedFrames = 0
  private(set) var validFrames = 0
  private(set) var validFrameBytes = 0
  private(set) var frameLengths: [Int: Int] = [:]
  private(set) var fragmentCounts: [Int: Int] = [:]
  private(set) var packetLengths: [Int: Int] = [:]
  private(set) var firstSequence: UInt16?
  private(set) var lastSequence: UInt16?

  private var previousSequence: UInt16?
  private var previousPacket: Data?
  private var expectedFragment: UInt8 = 0
  private var frame = Data()
  private var packetHasher = SHA256()
  private var frameHasher = SHA256()

  func consume(_ packet: Data) {
    packetHasher.update(data: packet)
    packetLengths[packet.count, default: 0] += 1
    guard packet.count > 3 else {
      malformedPackets += 1
      return
    }

    let sequence = UInt16(packet[packet.startIndex]) |
      (UInt16(packet[packet.startIndex + 1]) << 8)
    let fragment = packet[packet.startIndex + 2]
    let payload = packet.dropFirst(3)
    firstSequence = firstSequence ?? sequence
    lastSequence = sequence
    fragmentCounts[Int(fragment), default: 0] += 1

    if previousPacket == packet {
      duplicatePackets += 1
      return
    }

    guard fragment < 4 else {
      sequenceGaps += 1
      dropPartialIfPresent()
      remember(sequence, packet)
      return
    }

    if let previousSequence, sequence != previousSequence &+ 1 {
      sequenceGaps += 1
      let conflictingDuplicate = sequence == previousSequence
      dropPartialIfPresent()
      remember(sequence, packet)
      guard fragment == 0, !conflictingDuplicate else { return }
      begin(payload)
      return
    }
    remember(sequence, packet)

    if fragment == 0 {
      emitIfValid()
      begin(payload)
      return
    }

    guard !frame.isEmpty, fragment == expectedFragment else {
      sequenceGaps += 1
      dropPartialIfPresent()
      return
    }
    guard frame.count + payload.count <= 320 else {
      dropPartialIfPresent()
      return
    }
    frame.append(contentsOf: payload)
    expectedFragment = fragment &+ 1
  }

  func flush() {
    emitIfValid()
    previousSequence = nil
    previousPacket = nil
  }

  func summary() -> [String: Any] {
    [
      "sequenceGaps": sequenceGaps,
      "duplicatePackets": duplicatePackets,
      "malformedPackets": malformedPackets,
      "droppedFrames": droppedFrames,
      "validFrames": validFrames,
      "validFrameBytes": validFrameBytes,
      "firstSequence": firstSequence.map(Int.init) as Any,
      "lastSequence": lastSequence.map(Int.init) as Any,
      "packetLengths": dictionaryWithStringKeys(packetLengths),
      "fragmentCounts": dictionaryWithStringKeys(fragmentCounts),
      "frameLengths": dictionaryWithStringKeys(frameLengths),
      "notificationStreamSHA256": packetHasher.finalize().map { String(format: "%02x", $0) }.joined(),
      "validOpusFramesSHA256": frameHasher.finalize().map { String(format: "%02x", $0) }.joined(),
    ]
  }

  private func dictionaryWithStringKeys(_ source: [Int: Int]) -> [String: Int] {
    Dictionary(uniqueKeysWithValues: source.map { (String($0.key), $0.value) })
  }

  private func remember(_ sequence: UInt16, _ packet: Data) {
    previousSequence = sequence
    previousPacket = packet
  }

  private func begin(_ payload: Data.SubSequence) {
    guard !payload.isEmpty, payload.count <= 320 else {
      droppedFrames += 1
      discardPartial()
      return
    }
    frame = Data(payload)
    expectedFragment = 1
  }

  private func dropPartialIfPresent() {
    if !frame.isEmpty { droppedFrames += 1 }
    discardPartial()
  }

  private func discardPartial() {
    frame.removeAll(keepingCapacity: true)
    expectedFragment = 0
  }

  private func emitIfValid() {
    guard !frame.isEmpty else { return }
    let complete = frame
    discardPartial()
    guard Self.isPinnedOpusPacket(complete) else {
      droppedFrames += 1
      return
    }
    validFrames += 1
    validFrameBytes += complete.count
    frameLengths[complete.count, default: 0] += 1
    frameHasher.update(data: complete)
  }

  private static func isPinnedOpusPacket(_ packet: Data) -> Bool {
    guard packet.count >= 2, packet.count <= 320, let toc = packet.first else { return false }
    guard toc & 0x03 == 0, toc & 0x04 == 0 else { return false }
    let samplesAt16K: Int
    if toc & 0x80 != 0 {
      samplesAt16K = (16_000 << Int((toc >> 3) & 0x03)) / 400
    } else if toc & 0x60 == 0x60 {
      samplesAt16K = toc & 0x08 != 0 ? 320 : 160
    } else {
      samplesAt16K = (16_000 << Int((toc >> 3) & 0x03)) / 100
    }
    return samplesAt16K == 160
  }
}

private final class OmiBLEProbe: NSObject, CBCentralManagerDelegate, CBPeripheralDelegate {
  private let captureSeconds: TimeInterval
  private var central: CBCentralManager!
  private var peripheral: CBPeripheral?
  private var audioCharacteristic: CBCharacteristic?
  private var codecCharacteristic: CBCharacteristic?
  private var codec: Int?
  private var battery: Int?
  private var startedAt: Date?
  private var notificationCount = 0
  private var notificationBytes = 0
  private var gattServices: [[String: Any]] = []
  private var pendingCharacteristicDiscoveries = 0
  private var captureTimer: Timer?
  private var overallTimer: Timer?
  private var stopping = false
  private var finished = false
  private var stoppingReason = "capture_complete"
  private var stoppingExitCode: Int32 = 0
  private let metrics = FrameMetrics()

  init(captureSeconds: TimeInterval) {
    self.captureSeconds = min(20, max(10, captureSeconds))
    super.init()
    print("EVENT manager_create authorization=\(authorizationName(CBManager.authorization))")
    central = CBCentralManager(delegate: self, queue: .main, options: [
      CBCentralManagerOptionShowPowerAlertKey: false,
    ])
    overallTimer = Timer.scheduledTimer(withTimeInterval: 35, repeats: false) { [weak self] _ in
      self?.stop(reason: "overall_timeout", exitCode: 2)
    }
  }

  func centralManagerDidUpdateState(_ central: CBCentralManager) {
    print("EVENT central authorization=\(authorizationName(CBManager.authorization)) state=\(stateName(central.state))")
    guard central.state == .poweredOn else {
      if [.poweredOff, .unauthorized, .unsupported].contains(central.state) {
        stop(reason: "bluetooth_\(stateName(central.state))", exitCode: 2)
      }
      return
    }
    print("EVENT scan service=\(audioServiceUUID.uuidString)")
    central.scanForPeripherals(
      withServices: [audioServiceUUID],
      options: [CBCentralManagerScanOptionAllowDuplicatesKey: false]
    )
  }

  func centralManager(
    _ central: CBCentralManager,
    didDiscover peripheral: CBPeripheral,
    advertisementData: [String: Any],
    rssi RSSI: NSNumber
  ) {
    central.stopScan()
    self.peripheral = peripheral
    peripheral.delegate = self
    let identifierHash = String(sha256Hex(Data(peripheral.identifier.uuidString.utf8)).prefix(16))
    let advertisedServices = (advertisementData[CBAdvertisementDataServiceUUIDsKey] as? [CBUUID] ?? [])
      .map(\.uuidString).sorted()
    print("EVENT discovered idHash=\(identifierHash) rssi=\(RSSI) advertisedServices=\(advertisedServices)")
    central.connect(peripheral, options: nil)
  }

  func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
    print("EVENT connected")
    peripheral.discoverServices(nil)
  }

  func centralManager(
    _ central: CBCentralManager,
    didFailToConnect peripheral: CBPeripheral,
    error: Error?
  ) {
    stop(reason: "connect_failed:\(error?.localizedDescription ?? "unknown")", exitCode: 2)
  }

  func centralManager(
    _ central: CBCentralManager,
    didDisconnectPeripheral peripheral: CBPeripheral,
    error: Error?
  ) {
    if !finished {
      metrics.flush()
      finish(
        reason: stopping ? stoppingReason : "unexpected_disconnect",
        exitCode: stopping ? stoppingExitCode : 2
      )
    }
  }

  func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
    guard error == nil else {
      stop(reason: "service_discovery_failed:\(error!.localizedDescription)", exitCode: 2)
      return
    }
    let services = peripheral.services ?? []
    pendingCharacteristicDiscoveries = services.count
    print("EVENT services count=\(services.count) uuids=\(services.map { $0.uuid.uuidString }.sorted())")
    guard !services.isEmpty else {
      stop(reason: "no_services", exitCode: 2)
      return
    }
    for service in services {
      peripheral.discoverCharacteristics(nil, for: service)
    }
  }

  func peripheral(
    _ peripheral: CBPeripheral,
    didDiscoverCharacteristicsFor service: CBService,
    error: Error?
  ) {
    defer {
      pendingCharacteristicDiscoveries -= 1
      if pendingCharacteristicDiscoveries == 0 { maybeStartCapture() }
    }
    guard error == nil else {
      print("EVENT characteristic_error service=\(service.uuid.uuidString)")
      return
    }
    let characteristics = peripheral.services?
      .first(where: { $0.uuid == service.uuid })?.characteristics ?? service.characteristics ?? []
    let safeCharacteristics: [[String: Any]] = characteristics.map { characteristic in
      [
        "uuid": characteristic.uuid.uuidString,
        "properties": propertyNames(characteristic.properties),
      ]
    }
    gattServices.append([
      "uuid": service.uuid.uuidString,
      "characteristics": safeCharacteristics,
    ])
    print("EVENT characteristics service=\(service.uuid.uuidString) count=\(characteristics.count)")
    for characteristic in characteristics {
      switch characteristic.uuid {
      case audioDataUUID:
        audioCharacteristic = characteristic
      case codecUUID:
        codecCharacteristic = characteristic
        peripheral.readValue(for: characteristic)
      case batteryLevelUUID:
        peripheral.readValue(for: characteristic)
      default:
        break
      }
    }
  }

  func peripheral(
    _ peripheral: CBPeripheral,
    didUpdateValueFor characteristic: CBCharacteristic,
    error: Error?
  ) {
    guard error == nil, let data = characteristic.value else {
      print("EVENT value_error characteristic=\(characteristic.uuid.uuidString)")
      return
    }
    if characteristic.uuid == codecUUID {
      codec = data.first.map(Int.init)
      print("EVENT codec value=\(codec.map(String.init) ?? "empty")")
      maybeStartCapture()
      return
    }
    if characteristic.uuid == batteryLevelUUID {
      battery = data.first.map { min(100, Int($0)) }
      print("EVENT battery_read present=\(battery != nil)")
      return
    }
    guard characteristic.uuid == audioDataUUID, !stopping else { return }
    notificationCount += 1
    notificationBytes += data.count
    metrics.consume(data)
  }

  func peripheral(
    _ peripheral: CBPeripheral,
    didUpdateNotificationStateFor characteristic: CBCharacteristic,
    error: Error?
  ) {
    guard characteristic.uuid == audioDataUUID else { return }
    if let error {
      stop(reason: "notification_subscription_failed:\(error.localizedDescription)", exitCode: 2)
      return
    }
    if stopping, !characteristic.isNotifying {
      central.cancelPeripheralConnection(peripheral)
      return
    }
    guard characteristic.isNotifying, startedAt == nil else { return }
    startedAt = Date()
    print("EVENT capture_started seconds=\(Int(captureSeconds)) rawAudioPersisted=false")
    captureTimer = Timer.scheduledTimer(withTimeInterval: captureSeconds, repeats: false) { [weak self] _ in
      self?.stop(reason: "bounded_capture_elapsed", exitCode: 0)
    }
  }

  private func maybeStartCapture() {
    guard !stopping, startedAt == nil, pendingCharacteristicDiscoveries == 0,
          let peripheral, let audioCharacteristic else { return }
    guard audioCharacteristic.properties.contains(.notify) else {
      stop(reason: "audio_characteristic_not_notifiable", exitCode: 2)
      return
    }
    guard codec == 20 else {
      if codec != nil { stop(reason: "unsupported_codec_\(codec!)", exitCode: 2) }
      return
    }
    print("EVENT subscribe characteristic=\(audioDataUUID.uuidString)")
    peripheral.setNotifyValue(true, for: audioCharacteristic)
  }

  private func stop(reason: String, exitCode: Int32) {
    guard !finished, !stopping else { return }
    stopping = true
    central.stopScan()
    captureTimer?.invalidate()
    overallTimer?.invalidate()
    // The last notification can contain the final complete frame. Flush before deciding whether
    // the bounded capture produced usable Opus; otherwise a one-frame sample is falsely rejected.
    metrics.flush()
    var finalReason = reason
    var finalExitCode = exitCode
    if finalExitCode == 0, notificationCount == 0 {
      finalReason = "no_audio_notifications"
      finalExitCode = 2
    } else if finalExitCode == 0, metrics.validFrames == 0 {
      finalReason = "no_valid_opus_frames"
      finalExitCode = 2
    }
    stoppingReason = finalReason
    stoppingExitCode = finalExitCode
    if let peripheral, let audioCharacteristic, audioCharacteristic.isNotifying {
      print("EVENT unsubscribe")
      peripheral.setNotifyValue(false, for: audioCharacteristic)
      DispatchQueue.main.asyncAfter(deadline: .now() + 2) { [weak self] in
        guard let self, !self.finished else { return }
        self.central.cancelPeripheralConnection(peripheral)
        self.finish(reason: finalReason, exitCode: finalExitCode)
      }
      return
    }
    if let peripheral { central.cancelPeripheralConnection(peripheral) }
    finish(reason: finalReason, exitCode: finalExitCode)
  }

  private func finish(reason: String, exitCode: Int32) {
    guard !finished else { return }
    finished = true
    overallTimer?.invalidate()
    captureTimer?.invalidate()
    let elapsed = startedAt.map { Date().timeIntervalSince($0) }
    let output: [String: Any] = [
      "schema": 1,
      "reason": reason,
      "authorization": authorizationName(CBManager.authorization),
      "centralState": stateName(central.state),
      "serviceMatched": peripheral != nil,
      "codec": codec.map { $0 as Any } ?? NSNull(),
      "batteryRead": battery != nil,
      "captureSecondsRequested": captureSeconds,
      "captureSecondsActual": elapsed.map { $0 as Any } ?? NSNull(),
      "notificationCount": notificationCount,
      "notificationBytes": notificationBytes,
      "rawAudioPersisted": false,
      "gatt": gattServices,
      "packetMetrics": metrics.summary(),
    ]
    let data = try! JSONSerialization.data(withJSONObject: output, options: [.sortedKeys])
    print("RESULT \(String(data: data, encoding: .utf8)!)")
    fflush(stdout)
    exit(exitCode)
  }
}

private final class ProbeAppDelegate: NSObject, NSApplicationDelegate {
  private let captureSeconds: TimeInterval
  private var probe: OmiBLEProbe?
  private var window: NSWindow?
  private var statusLabel: NSTextField?
  private var startButton: NSButton?

  init(captureSeconds: TimeInterval) {
    self.captureSeconds = captureSeconds
  }

  func applicationDidFinishLaunching(_ notification: Notification) {
    print("EVENT app_ready awaiting_explicit_start=true")
    let window = NSWindow(
      contentRect: NSRect(x: 0, y: 0, width: 440, height: 190),
      styleMask: [.titled, .closable],
      backing: .buffered,
      defer: false
    )
    window.title = "Anticipy Omi BLE Probe"
    let label = NSTextField(labelWithString: "No scan has started. Press Start to check the official Omi audio service. No raw audio is saved.")
    label.alignment = .center
    label.maximumNumberOfLines = 3
    label.frame = NSRect(x: 25, y: 88, width: 390, height: 60)
    window.contentView?.addSubview(label)
    let button = NSButton(title: "Start bounded Omi test", target: self, action: #selector(startProbe))
    button.bezelStyle = .rounded
    button.frame = NSRect(x: 120, y: 38, width: 200, height: 34)
    window.contentView?.addSubview(button)
    window.center()
    window.makeKeyAndOrderFront(nil)
    self.window = window
    self.statusLabel = label
    self.startButton = button
    NSApp.activate(ignoringOtherApps: true)
  }

  @objc private func startProbe() {
    guard probe == nil else { return }
    startButton?.isEnabled = false
    statusLabel?.stringValue = "Scanning after your Start click. The test stops automatically."
    print("EVENT explicit_start")
    probe = OmiBLEProbe(captureSeconds: captureSeconds)
  }
}

private let secondsArgument = CommandLine.arguments
  .dropFirst()
  .first.flatMap(Double.init) ?? 12
// Mirror all probe output to a file so an autonomous run can read the result afterwards.
// READ-ONLY: this file contains no writeValue call and never touches the DFU control point 1531.
private let reconLogPath = ("~/anticipy-pendant-restore/tools/recon/RECON_RESULT.txt" as NSString)
  .expandingTildeInPath
freopen(reconLogPath, "w", stdout)
setvbuf(stdout, nil, _IONBF, 0)

private let application = NSApplication.shared
application.setActivationPolicy(.regular)
private let appDelegate = ProbeAppDelegate(captureSeconds: secondsArgument)
application.delegate = appDelegate
application.run()

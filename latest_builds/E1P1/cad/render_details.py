from pathlib import Path
p=Path(__file__).resolve().parent/'build_oval_e1.py'
exec(compile(p.read_text().split('checks=[]')[0],str(p),'exec'))
INK='#223a46';MUTED='#5b6b74';WARN='#9a5c32';OUT=HERE
exec(compile((HERE/'source_inputs/render_helpers.py').read_text(),str(HERE/'source_inputs/render_helpers.py'),'exec'))
metrics={'source_sha256':SOURCE_SHA,'screw_clearances_mm':{},'native_coordinates':'CAD X=nativeX, CAD Y=-nativeY, Zup','battery_candidate':'Jauch LP561836JU+PCM+2 WIRES50MM','battery_max_mm':[38.5,18.5,6.0],'nominal_main_body_mm':[P['L'],P['W'],P['H']],'PCB_bottom_z_mm':P['pcb_bottom'],'PCB_top_z_mm':BT,'battery_top_z_mm':P['battery_z']+6.,'PCB_locator_side_clearance_mm':.35,'microphone_port_native_XY_mm':[portx,porty],'USB_socket_front_native_XY_mm':[19.7,30.],'USB_socket_front_recess_at_center_mm':19.7-(P['center_x']-P['L']/2),'USB_gauge_cross_section_mm':[10.8,6.5],'USB_opening_cross_section_mm':[11.4,7.1],'button_stroke_planning_mm':.5,'minimum_stock_battery_lead_length_mm':45,'NTC_MPN':'B57540G1103F000','NTC_glass_max_diameter_and_length_mm':[.8,1.4],'NTC_insulated_attachment_gauge_mm':[2.,1.4,1.0],'NTC_first_bend_from_glass_ends_mm':[4.9,4.7],'NTC_minimum_bend_radius_mm':.75,'wire_OD_and_exit_status':'Unapproved installation gauges; actual battery lead exits are not dimensioned by supplier'}
for pp in parts:
 if pp['kind']=='hardware':metrics['screw_clearances_mm'][pp['name']]={'to_battery_installation_guard':pp['shape'].distance(battery_install),'to_PCB':pp['shape'].distance(pcb),'to_nearest_expanded_component':min(pp['shape'].distance(s)for s in inflated.values())}
(HERE/'Oval_Mechanical_Details.json').write_text(json.dumps(metrics,indent=2)+'\n')
f=canvas('Anticipy / ports and controls','Exact assembled CAD. The front surface curves; the real USB-C socket remains accessible at the short end.',(15,10));ax,proj=picture(f,[.02,.11,.96,.75],parts,elev=38,azim=-130,size=1600,pad=.16)
note(ax,proj,(17,-30,BT-.4),'USB-C port — charging disabled\n11.4 × 7.1 mm passage',(.04,.42))
note(ax,proj,(portx,-porty,13.5),'Top microphone\n1.2 mm sound opening',(.69,.84))
note(ax,proj,(ledx,-ledy,14.1),'LED window\nClear retained lightpipe',(.60,.13))
note(ax,proj,(sx,-sy,14.1),'Push button\nFlush, internally retained',(.02,.16))
f.text(.04,.04,'Gold is display color. Use unfilled nonconductive polymer for the fit prototype; coatings, acoustics and RF require physical testing.',fontsize=11,color=WARN);save(f,'Oval_E1_Port_and_Controls.png')
expl=[]
for pp in parts:
 dz=43 if pp['name']=='Front_oval_shell' or pp['kind']in['control','adhesive','seal','board_pad'] else -4 if pp['name']=='Rear_service_cover' or pp['kind']=='hardware' else 9 if pp['kind']in['part','pcb'] else 0
 dx=-23 if pp['kind']=='motor'else 0
 if pp['kind']=='motor':dz=4
 expl.append(dict(pp,shape=pp['shape'].translate((dx,0,dz))))
f=canvas('Anticipy / what goes inside','Exploded view of the checked geometry. Parts are lifted apart; the motor is moved left for visibility. Use the assembled STEP for actual positions.',(15,12));ax,proj=picture(f,[.02,.10,.96,.80],expl,elev=25,azim=-65,size=1600,pad=.12)
note(ax,proj,(44,-31,57.8),'Curved front shell\nMic, LED and button',(.69,.91))
note(ax,proj,(59.5,-29.5,21),'Bluetooth radio module\nAntenna end stays clear',(.72,.65))
note(ax,proj,(35.2,-28.6,20),'Exact E1 PCB\n45.75 × 17.88 × 0.8 mm',(.03,.65))
note(ax,proj,(49,-40,7),'Protected battery\n38.5 × 18.5 × 6.0 mm max',(.72,.43))
note(ax,proj,(15,-20.45,7),'Haptic motor\n10.6 mm installation gauge',(.02,.42))
note(ax,proj,(53,-31,8.1),'Battery / motor / NTC wires\nRoutes shown at actual assembly height',(.70,.27))
note(ax,proj,(49,-43,-2.8),'Rear cover, PCB guide and supports\nTwo recessed M2 × 4 mm screws',(.07,.14))
f.text(.04,.04,'350 mAh minimum battery is a candidate, not a proven 16-hour unit. Wire diameters, terminal exits, sensor and fasteners require supplier approval.',fontsize=11,color=WARN);save(f,'Oval_E1_Exploded_Labeled.png')
ex=cq.Assembly(name='OVAL_E1_EXPLODED_PRESENTATION_ONLY')
for pp in expl:ex.add(pp['shape'],name=pp['name'],color=cq.Color(*to_rgb(pp['color'])))
ex.save(str(HERE/'Oval_E1_Exploded_VIEW_ONLY.step'))
print(json.dumps(metrics,indent=2))

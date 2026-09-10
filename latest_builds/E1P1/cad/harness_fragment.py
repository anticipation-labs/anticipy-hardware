# Executed inside builder; nominal routing gauges, not manufacturer wire-exit dimensions.
def V(p):return cq.Vector(p[0],-p[1],p[2])
def wire_from_edges(edges,od):
    path=cq.Wire.assembleEdges(edges);e=edges[0];pl=cq.Plane(origin=e.startPoint(),normal=e.tangentAt(0))
    return cq.Workplane(pl).circle(od/2).sweep(cq.Workplane(obj=path),isFrenet=True).val()
def rounded_polyline(points,r):
    pp=[V(p)for p in points];edges=[];prev=pp[0]
    for i in range(1,len(pp)-1):
        u=(pp[i]-pp[i-1]).normalized();v=(pp[i+1]-pp[i]).normalized();theta=math.acos(max(-1,min(1,u.dot(v))))
        if theta<1e-7:continue
        d=r*math.tan(theta/2)
        if d>(pp[i]-pp[i-1]).Length*.499 or d>(pp[i+1]-pp[i]).Length*.499:raise ValueError('Insufficient straight segment for specified wire bend')
        a=pp[i]-u*d;b=pp[i]+v*d;center=pp[i]+(v-u).normalized()*(r/math.cos(theta/2));mid=center+((a-center)+(b-center)).normalized()*r
        if (a-prev).Length>1e-7:edges.append(cq.Edge.makeLine(prev,a))
        edges.append(cq.Edge.makeThreePointArc(a,mid,b));prev=b
    if (pp[-1]-prev).Length>1e-7:edges.append(cq.Edge.makeLine(prev,pp[-1]))
    return edges
# Factory wires leave selected pack short end. Their precise positions are not dimensioned.
# Planning exit levels4.1mm, center offsets±1.1mm; supplier must confirm without bending a cell tab.
for name,ye,targety,cornerx,col in [('BATTERY_NEG',by-.2,27.665,34.,'#323b3f'),('BATTERY_POS',by+1.8,28.935,39.,'#a85846')]:
    x0=bx-bl/2
    start=V((x0,ye,4.1));mid=V((x0-2,ye,6.1));end=V((x0,ye,8.1))
    edges=[cq.Edge.makeThreePointArc(start,mid,end)]
    edges+=rounded_polyline([(x0,ye,8.1),(cornerx,ye,8.1),(cornerx+5,targety,8.1),(54.9,targety,8.1)],2.)
    lead=wire_from_edges(edges,1.2);add(name+'_wire_OD1p2_R2_PLANNING',lead,'wire',col,'Factory exit coordinates/OD not on pack drawing. 1.2mmOD and2mmcenterline bend are planning. Shorten only insulated factory leads, no cell/PCM modification.')
    joint=cyl(54.9,targety,8.35,1.0,.75);add(name+'_PCB_joint_guard',joint,'joint',col,'Local solder/strain-relief gauge ends at actual underside pad.')
# Specified TDK B57540G1103F000: glass bodyD0.8max xL1.4max.
# Insulation/tape uses2x1.4x1.0mm gauge; first bend4.9/4.7mmfromglass ends, R0.75min.
ntcy=34.235
ntc=box(49.3,ntcy,7.5,2.0,1.4,1.0);add('Separate_10k_NTC_TDK_G1540_insulated_MAX_PLANNING',ntc,'ntc','#8a6446','Specified B57540G1103F000 glassbeadD0.8x1.4max; insulated/taped2x1.4x1.0mmguard. Supplier mustconfirm finalinsulationthickness.')
ed1=[cq.Edge.makeLine(V((50.0,ntcy,8.0)),V((54.9,ntcy,8.0))),cq.Edge.makeThreePointArc(V((54.9,ntcy,8.0)),V((55.65,ntcy-.75,8.0)),V((54.9,32.735,8.0)))]
ed2=[cq.Edge.makeLine(V((48.6,ntcy,8.0)),V((43.9,ntcy,8.0))),cq.Edge.makeThreePointArc(V((43.9,ntcy,8.0)),V((43.15,ntcy-.75,8.0)),V((43.9,32.735,8.0)))]+rounded_polyline([(43.9,32.735,8.0),(47.,32.735,8.0),(52.,31.465,8.0),(54.9,31.465,8.0)],.75)
for i,(ed,targety)in enumerate([(ed1,32.735),(ed2,31.465)],1):
    add(f'NTC_wire_{i}_OD0p5_R0p75_PLANNING',wire_from_edges(ed,.5),'wire','#997346','0.15mmfactorylead inside0.5mminsulationgauge; R0.75 bends at least4.7mmfromglassend. Insulation/spliceprocess stillrequiresapproval.')
    add(f'NTC_PCB_joint_{i}_guard',cyl(54.9,targety,8.25,.9,.85),'joint','#997346')
# Existing ERM motor factorylead route; fine wire dimensions are still a gauge.
for i,(yy,targety,xrise,ycross,xturn)in enumerate([(my-.65,36.735,51.,25.95,58.5),(my+.65,35.465,49.5,26.55,57.)],1):
    pts=[(mx+5.3,yy,3.0),(xrise,yy,3.0),(xrise,yy,8.0),(xrise,ycross,8.0),(xturn,ycross,8.0),(xturn,targety,8.0),(54.9,targety,8.0)]
    add(f'MOTOR_wire_{i}_OD0p5_R1_PLANNING',wire_from_edges(rounded_polyline(pts,1.),.5),'wire','#b8994e','0.5mmOD and1mmcenterline bend gauge; motor supplier lead exit not yet released.')
    add(f'MOTOR_PCB_joint_{i}_guard',cyl(54.9,targety,8.25,.9,.85),'joint','#b8994e')

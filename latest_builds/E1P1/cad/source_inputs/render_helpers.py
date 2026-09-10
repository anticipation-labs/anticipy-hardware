def render(pp, elev=35, azim=-65, size=1300, pad=0.08):
    (el, az) = map(math.radians, (elev, azim))
    eye = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    right = np.array([-math.sin(az), math.cos(az), 0.0])
    up = np.cross(eye, right)
    T = np.stack([right, up, eye], axis=1)
    meshes = []
    for p in pp:
        (vv, tt) = p['shape'].tessellate(0.035, 0.1)
        if not vv:
            continue
        meshes.append((p, np.array([[v.x, v.y, v.z] for v in vv]), np.array(tt)))
    allp = np.concatenate([v @ T for (p, v, t) in meshes])
    lo = allp[:, :2].min(0)
    hi = allp[:, :2].max(0)
    scale = size * (1 - 2 * pad) / max(hi - lo)
    center = (hi + lo) / 2

    def project(point):
        q = np.array(point) @ T
        return ((q[:2] - center) * scale + size / 2) * np.array([1, -1]) + np.array([0, size])
    color = np.full((size, size, 3), 249.0, dtype=float)
    depth = np.full((size, size), -np.inf)
    light = eye + up * 0.7 + right * 0.3
    light /= np.linalg.norm(light)
    for (p, v, tri) in meshes:
        q = v @ T
        q[:, :2] = (q[:, :2] - center) * scale + size / 2
        q[:, 1] = size - q[:, 1]
        rgb = np.array(to_rgb(p['color'])) * 255
        for t in tri:
            (a, b, c) = q[t]
            x0 = max(0, int(np.floor(min(a[0], b[0], c[0]))))
            x1 = min(size - 1, int(np.ceil(max(a[0], b[0], c[0]))))
            y0 = max(0, int(np.floor(min(a[1], b[1], c[1]))))
            y1 = min(size - 1, int(np.ceil(max(a[1], b[1], c[1]))))
            if x1 < x0 or y1 < y0:
                continue
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-12:
                continue
            (yy, xx) = np.mgrid[y0:y1 + 1, x0:x1 + 1]
            xx = xx + 0.5
            yy = yy + 0.5
            u = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / den
            w = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / den
            k = 1 - u - w
            z = u * a[2] + w * b[2] + k * c[2]
            cut = depth[y0:y1 + 1, x0:x1 + 1]
            mask = (u >= -1e-07) & (w >= -1e-07) & (k >= -1e-07) & (z > cut)
            if not mask.any():
                continue
            normal = np.cross(v[t[1]] - v[t[0]], v[t[2]] - v[t[0]])
            norm = np.linalg.norm(normal)
            shade = 0.69 + 0.31 * abs(np.dot(normal, light) / norm) if norm else 1
            cut[mask] = z[mask]
            color[y0:y1 + 1, x0:x1 + 1][mask] = rgb * shade
    return (color.clip(0, 255).astype('uint8'), project)

def canvas(title, subtitle, sz=(15, 10)):
    f = plt.figure(figsize=sz, facecolor='#f9f9f9')
    f.text(0.04, 0.945, title, fontsize=26, weight='bold', color=INK)
    f.text(0.04, 0.902, subtitle, fontsize=12, color=MUTED)
    return f

def picture(f, rect, pp, crop=False, **kw):
    (im, proj) = render(pp, **kw)
    ax = f.add_axes(rect)
    ax.imshow(im)
    ax.set_xlim(0, len(im))
    ax.set_ylim(len(im), 0)
    ax.axis('off')
    if crop:
        (yy, xx) = np.where((im != 249).any(axis=2))
        margin = 65
        ax.set_xlim(xx.min() - margin, xx.max() + margin)
        ax.set_ylim(yy.max() + margin, yy.min() - margin)
    return (ax, proj)

def note(ax, proj, point, text, xy, align='left'):
    ax.annotate(text, xy=proj(point), xytext=xy, textcoords='axes fraction', fontsize=11, color=INK, ha=align, va='center', bbox=dict(boxstyle='round,pad=.4', fc='#f9f9f9', ec='none', alpha=0.98), arrowprops=dict(arrowstyle='-', color='#85929b', lw=1, connectionstyle='angle3,angleA=0,angleB=90'))

def save(f, name):
    f.savefig(OUT / name, dpi=150)
    plt.close(f)

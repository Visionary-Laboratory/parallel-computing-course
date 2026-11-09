#!/usr/bin/env python3
"""Render an actual 2D Gaussian image approximation and an explanatory film.

Optional authoring dependencies: NumPy, Pillow, ffmpeg. Site playback needs none.
No target-image overlay is used in the reconstructed picture, including the end.
"""
from pathlib import Path
import argparse, hashlib, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
MEDIA = HERE / 'media'
GREEN = (23, 102, 83)
INK = (37, 62, 46)
MUTED = (99, 122, 109)
W, H = 480, 312
FPS, DURATION = 24, 44


def footprint(g):
    x, y, sx, sy, angle, opacity = g[:6]
    radius = 3.5 * max(sx, sy)
    x0, x1 = max(0, math.floor(x-radius)), min(W, math.ceil(x+radius)+1)
    y0, y1 = max(0, math.floor(y-radius)), min(H, math.ceil(y+radius)+1)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    c, s = math.cos(angle), math.sin(angle)
    u = c*(xx-x)+s*(yy-y)
    v = -s*(xx-x)+c*(yy-y)
    a = opacity*np.exp(-.5*((u/sx)**2+(v/sy)**2))
    return (slice(y0, y1), slice(x0, x1)), a.astype(np.float32)[..., None]


def paint(image, g):
    region, a = footprint(g)
    image[region] = (1-a)*image[region]+a*np.asarray(g[6:9], dtype=np.float32)


def fit(target):
    """Greedy, coarse-to-fine 2D alpha-composited fit; not 3DGS training."""
    current = np.ones_like(target)
    gaussians = []
    gray = target.mean(axis=2)
    dy, dx = np.gradient(gray)
    rng = np.random.default_rng(43)

    def append(shape):
        region, a = footprint(shape)
        # Least-squares optimal constant RGB for this fixed alpha footprint.
        residual = target[region]-(1-a)*current[region]
        color = np.clip((a*residual).sum(axis=(0, 1))/(a*a).sum(), 0, 1)
        g = [*shape, *color.tolist()]
        paint(current, g)
        gaussians.append(g)

    append([W/2, H/2, 65, 25, -25*math.pi/180, .8])
    levels = []
    for step in [72, 36, 18, 9, 4.5, 2.25, 1.125]:
        centers = [(x, y) for y in np.arange(step/2, H, step)
                   for x in np.arange(step/2, W, step)]
        rng.shuffle(centers)
        for x, y in centers:
            ix, iy = int(x), int(y)
            gx = dx[max(0, iy-2):iy+3, max(0, ix-2):ix+3]
            gy = dy[max(0, iy-2):iy+3, max(0, ix-2):ix+3]
            a, b, d = float((gx*gx).mean()), float((gx*gy).mean()), float((gy*gy).mean())
            coherence = math.hypot(a-d, 2*b)/(a+d+1e-8)
            angle = .5*math.atan2(2*b, a-d)+math.pi/2
            append([float(x), float(y), step*.8, step*(.8-.25*coherence), angle, .95])
        levels.append(len(gaussians))
        print('Fitted', len(gaussians), 'Gaussians', flush=True)
    mse = float(np.mean((current-target)**2))
    return gaussians, current, levels, -10*math.log10(mse)


def smooth(v):
    v = min(1, max(0, v))
    return v*v*(3-2*v)


def interpolate(t, values):
    for (a, av), (b, bv) in zip(values, values[1:]):
        if t <= b:
            u = smooth((t-a)/(b-a))
            return av+(bv-av)*u
    return values[-1][1]


def properties(t):
    sx, sy, angle, opacity = 65., 25., -25., .8
    if t < 4:
        sx = interpolate(t, [(0, 30), (2.5, 100), (4, 65)])
        angle = 0
    elif t < 8:
        sy = interpolate(t, [(4, 25), (6.5, 65), (8, 25)])
        angle = 0
    elif t < 12:
        angle = interpolate(t, [(8, 0), (10, 75), (12, -25)])
    elif t < 16:
        opacity = interpolate(t, [(12, .8), (13.5, .2), (15, 1), (16, .8)])
    return sx, sy, angle, opacity


def encode(gaussians, final, target, font_path):
    fonts = {s: ImageFont.truetype(font_path, s) for s in (16, 18, 20, 23, 28, 34)}
    def label(draw, xy, value, size=20, color=INK):
        draw.text(xy, value, font=fonts[size], fill=color)

    movie = MEDIA/'gaussian-build.mp4'
    proc = subprocess.Popen(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1120x760', '-r', str(FPS),
        '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(movie)], stdin=subprocess.PIPE)
    current = np.ones_like(final)
    painted = 0
    checkpoints = [(18, 1), (21, 16), (24, 128), (27, 768), (31, 3000), (35, 12000), (40, len(gaussians))]
    snapshots = {}
    for frame in range(FPS*DURATION):
        t = frame/FPS
        canvas = Image.new('RGB', (1120, 760), '#fafcfb')
        draw = ImageDraw.Draw(canvas)
        section = min(4, int(t/4)) if t < 16 else 4
        titles = ['① 拉长主轴', '② 改变次轴宽度', '③ 旋转高斯', '④ 改变不透明度', '⑤ 更多高斯，共同构成图像']
        label(draw, (36, 25), titles[section], 34)
        subtitles = ['只改变主轴尺度，其余参数保持不变。', '只改变次轴尺度，椭圆逐渐变圆，再变扁。',
                      '尺度不变，覆盖方向随角度改变。', '几何形状不变，同一位置的贡献变强或变弱。',
                      '每个新高斯都带着位置、形状、颜色和不透明度加入合成。']
        label(draw, (38, 77), subtitles[section], 20, MUTED)
        sx, sy, angle, opacity = properties(t)
        if t < 18:
            picture = np.ones_like(final)
            color = np.asarray(GREEN)/255
            if t >= 16:
                u = smooth((t-16)/2)
                color = color*(1-u)+np.asarray(gaussians[0][6:])*u
            paint(picture, [W/2, H/2, sx, sy, angle*math.pi/180, opacity, *color])
            count = 1
        else:
            count = round(interpolate(t, checkpoints))
            while painted < count:
                paint(current, gaussians[painted])
                painted += 1
            picture = current
        image = Image.fromarray(np.uint8(np.clip(picture, 0, 1)*255))
        image = image.resize((720, 468), Image.Resampling.LANCZOS)
        canvas.paste(image, (36, 132))
        draw.rounded_rectangle((35, 131, 757, 601), 4, outline='#d1dfd5', width=2)
        if t < 16:
            for i, (name, value) in enumerate([('主轴尺度', f'{sx:.0f}'), ('次轴尺度', f'{sy:.0f}'), ('旋转角度', f'{angle:.0f}°'), ('不透明度', f'{opacity:.2f}')]):
                y = 150+i*88
                draw.rounded_rectangle((788, y, 1080, y+72), 8, fill='#e5f0e8' if i==section else '#f0f4f1', outline='#9ebdab' if i==section else '#e0e9e3')
                label(draw, (806, y+12), name, 20)
                label(draw, (984, y+12), value, 28, GREEN)
            label(draw, (790, 532), '一次改变一个属性', 20, GREEN)
            label(draw, (790, 565), '观察变化来自哪里', 18, MUTED)
        else:
            label(draw, (790, 142), '已叠加的高斯', 23)
            label(draw, (790, 180), f'{count:,}', 34, GREEN)
            label(draw, (790, 250), '目标照片 · Garden', 18, MUTED)
            ref = Image.fromarray(np.uint8(target*255)).resize((290, 189), Image.Resampling.LANCZOS)
            canvas.paste(ref, (790, 282))
            label(draw, (790, 500), '左侧始终是高斯合成结果', 18, GREEN)
            label(draw, (790, 533), '从粗略色块到可辨认的细节', 18, MUTED)
        footer = '不透明度改变贡献强弱；两个尺度和旋转决定覆盖形状。' if t < 16 else '颜色与位置也各不相同，许多局部贡献重叠后形成完整画面。'
        label(draw, (38, 623), footer, 23)
        label(draw, (38, 666), '二维图像拟合演示；三维高斯需要先投影到成像平面，再进行合成。', 18, MUTED)
        draw.rounded_rectangle((38, 716, 1080, 723), 3, fill='#dfe8e2')
        if t > 0:
            draw.rectangle((38, 716, 38+1042*min(t/40, 1), 723), fill=GREEN)
        if frame in (0, 16*FPS, 24*FPS, 31*FPS, 40*FPS):
            snapshots[int(t)] = canvas.copy()
        proc.stdin.write(canvas.tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError('ffmpeg failed')
    snapshots[0].save(MEDIA/'gaussian-build-poster.jpg', quality=92)
    snapshots[40].save(MEDIA/'gaussian-build-final.jpg', quality=92)
    # Print shows key frames instead of an inert player.
    strip = Image.new('RGB', (1120, 760), 'white')
    for i, key in enumerate((0, 24, 31, 40)):
        strip.paste(snapshots[key].resize((560, 380), Image.Resampling.LANCZOS), ((i%2)*560, (i//2)*380))
    strip.save(MEDIA/'gaussian-build-stages.jpg', quality=94)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--font', default='/System/Library/Fonts/STHeiti Light.ttc')
    ap.add_argument('--fit-only', action='store_true')
    args = ap.parse_args()
    source = MEDIA/'garden-0.jpg'
    target = np.asarray(Image.open(source).convert('RGB').resize((W, H), Image.Resampling.LANCZOS), dtype=np.float32)/255
    gs, final, levels, psnr = fit(target)
    print('PSNR against resized target:', round(psnr, 2), 'dB', flush=True)
    np.savez_compressed('/private/tmp/gaussian-film-fit.npz', gaussians=np.asarray(gs), target=target, final=final)
    Image.fromarray(np.uint8(np.clip(final, 0, 1)*255)).save('/private/tmp/gaussian-film-fit.png')
    metadata = dict(gaussians=len(gs), levels=levels, width=W, height=H, duration=DURATION, fps=FPS,
        psnr_db=round(psnr, 3), source='garden-0.jpg', source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        method='Greedy multiscale 2D Gaussian source-over fitting; target shown separately, never overlaid on reconstruction.')
    (MEDIA/'gaussian-build.json').write_text(json.dumps(metadata, indent=2)+'\n')
    if not args.fit_only:
        encode(gs, final, target, args.font)


if __name__ == '__main__':
    main()

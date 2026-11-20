#!/usr/bin/env python3
"""Starman icon set. Edit ICONS below, then run:  python3 tools/build_icons.py
Writes assets/icons/<name>.svg and <name>.fill.svg, and rebuilds the Icons chapter in index.html.

Each icon is a list of (kind, svg) parts on a 24-unit grid, line 1.5:
  b   body: a closed shape. Outlined normally, solid in the filled version.
  d   detail drawn on the body. A line normally, cut out of the solid body when filled.
  ds  as d, but shown lighter (secondary) in the outline version.
  dp  solid detail (a dot or patch). Solid normally, cut out when filled.
  dc  small solid detail, cut out at its exact size when filled (dp grows by the line width).
  dh  ring detail. A ring normally, a cut-out hole when filled.
  o   open line that is not part of a body. Same in both versions.
  s   secondary open line, shown lighter in both versions.
  p   solid dot outside a body. Same in both versions.
"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = lambda x, y, r, cls='': f'<circle{cls} cx="{x}" cy="{y}" r="{r}"/>'
P = lambda d: f'<path d="{d}"/>'
ICONS = {
 'lap':      [('b', P('M6.5 4.5h6.25a3.25 3.25 0 0 1 3.25 3.25v1.5a2.25 2.25 0 0 0 2.25 2.25 2.25 2.25 0 0 1 2.25 2.25v2.5a3.25 3.25 0 0 1-3.25 3.25H6.5a3 3 0 0 1-3-3v-9a3 3 0 0 1 3-3z')), ('d', P('M10.5 16v3.5'))],
 'timer':    [('b', C(12, 13.5, 7.25)), ('o', P('M10 2.75h4M12 2.75v3.5M17.9 7.1l1.1-1.1')), ('d', P('M12 13.5l2.7-2.7'))],
 'sectors':  [('o', P('M14.86 4.03A8.5 8.5 0 0 1 20.08 14.63')), ('s', P('M18.32 17.69a8.5 8.5 0 0 1-12.64 0M3.92 14.63A8.5 8.5 0 0 1 9.14 4.03'))],
 'delta':    [('b', P('M12 4.75l8.25 14.25H3.75z'))],
 'telemetry':[('o', P('M3 14.5l3.5-4.5 3.5 3.5 4-8.5 3 6 4-3.5')), ('s', P('M3 19.25h18'))],
 'speed':    [('b', C(12, 12, 8.75)), ('ds', P('M6.75 12h.01M8.3 8.3h.01M12 6.75h.01M17.25 12h.01')), ('d', P('M12 12.5l3.3-4.1')), ('dp', C(12, 12.5, 1.5))],
 'g-force':  [('b', C(12, 12, 8.75)), ('ds', P('M12 7.25v9.5M7.25 12h9.5')), ('dp', C(15.4, 8.6, 1.6))],
 'apex':     [('o', P('M4.5 20.25V12a7.5 7.5 0 0 1 7.5-7.5h8.25')), ('s', P('M10.25 20.25V13a2.75 2.75 0 0 1 2.75-2.75h7.25')), ('p', C(10.9, 10.9, 1.6))],
 'gears':    [('o', P('M6 5.5v13M12 5.5v13M18 5.5V12M6 12h12'))],
 'tyre':     [('b', C(12, 12, 8.75)), ('ds', '<circle cx="12" cy="12" r="6" stroke-dasharray="1.4 2.37"/>'), ('dh', C(12, 12, 2.75))],
 'temp':     [('b', P('M12 3.25a2.25 2.25 0 0 1 2.25 2.25v7.85a4.25 4.25 0 1 1-4.5 0V5.5A2.25 2.25 0 0 1 12 3.25z')), ('d', P('M12 8.5v6.5')), ('dp', C(12, 17, 1.75))],
 'fuel':     [('b', '<rect x="4.5" y="3.5" width="9.5" height="17" rx="2"/>'), ('dh', '<rect x="7" y="6.5" width="4.5" height="4" rx=".75"/>'), ('o', P('M3.25 20.5h12M14 9.75h1.25a2 2 0 0 1 2 2v4.75a1.5 1.5 0 0 0 3 0V9.25L18 6.75'))],
 'wheel':    [('b', P('M12 5.5c2.6 0 5 .2 6.9.7 1.8.5 2.85 2.9 2.85 5.6 0 2.4-.7 4.7-1.6 6.4a1.25 1.25 0 0 1-2.25-.95l.55-1.7a.8.8 0 0 0-.75-1.05h-1a1.1 1.1 0 0 0-1.1 1.1v.55a1.1 1.1 0 0 1-1.1 1.1H9.5a1.1 1.1 0 0 1-1.1-1.1v-.55a1.1 1.1 0 0 0-1.1-1.1h-1a.8.8 0 0 0-.75 1.05l.55 1.7a1.25 1.25 0 0 1-2.25.95c-.9-1.7-1.6-4-1.6-6.4 0-2.7 1.05-5.1 2.85-5.6C7 5.7 9.4 5.5 12 5.5z')), ('dh', '<rect x="8.75" y="7.9" width="6.5" height="3.4" rx=".8"/>'), ('dc', C(9.9, 13.9, .65)), ('dc', C(12, 13.9, .65)), ('dc', C(14.1, 13.9, .65))],
 'helmet':   [('b', P('M12 4a8.25 8.25 0 0 0-8.25 8.25v2.25a4 4 0 0 0 4 4h8a4.5 4.5 0 0 0 4.5-4.5v-1.75A8.25 8.25 0 0 0 12 4z')), ('d', P('M20.25 11h-5.5a2 2 0 0 0 0 4h5.5'))],
 'car':      [('o', P('M5.25 11l1.35-4.1a2 2 0 0 1 1.9-1.4h7a2 2 0 0 1 1.9 1.4L18.75 11M6.25 17v1.75M17.75 17v1.75')), ('b', '<rect x="3.25" y="11" width="17.5" height="6" rx="2"/>'), ('dp', C(7, 14, 1.1)), ('dp', C(17, 14, 1.1))],
 'flag':     [('o', P('M5 21V3.25')), ('b', P('M5 4.25h14l-2.25 4.5 2.25 4.5H5z')), ('dp', P('M8.5 4.25H12v4.5H8.5zM12 8.75h3.5v4.5H12z'))],
 'podium':   [('b', P('M3 19.75V14.5h6V8.75h6V12h6v7.75z')), ('ds', P('M9 14.5v5.25M15 12v7.75'))],
 'standings':[('o', P('M10 6.5h10.25M10 12h7.25M10 17.5h4.25')), ('p', C(5, 6.5, 1.5)), ('p', C(5, 12, 1.5)), ('p', C(5, 17.5, 1.5))],
 'circuit':  [('b', P('M12 21.25s6.75-5.9 6.75-11.5a6.75 6.75 0 0 0-13.5 0c0 5.6 6.75 11.5 6.75 11.5z')), ('dh', C(12, 9.75, 2.4))],
 'onboard':  [('b', '<rect x="2.75" y="6.5" width="13" height="11" rx="3"/>'), ('b', P('M15.75 10.5l4.3-2.6a.8.8 0 0 1 1.2.7v6.8a.8.8 0 0 1-1.2.7l-4.3-2.6z'))],
 'live':     [('o', P('M8.1 8.1a5.5 5.5 0 0 0 0 7.8M15.9 8.1a5.5 5.5 0 0 1 0 7.8')), ('s', P('M5.3 5.3a9.5 9.5 0 0 0 0 13.4M18.7 5.3a9.5 9.5 0 0 1 0 13.4')), ('p', C(12, 12, 1.9, ' class="dot"'))],
 'coach':    [('b', P('M6 4.25h12a3 3 0 0 1 3 3v6.5a3 3 0 0 1-3 3h-5.25l-3.9 3.15a.5.5 0 0 1-.85-.4v-2.75H6a3 3 0 0 1-3-3v-6.5a3 3 0 0 1 3-3z')), ('d', P('M9 9.25v2.5M12 8v5M15 9.25v2.5'))],
 'notes':    [('b', P('M7.5 3.25h6.35a2 2 0 0 1 1.4.6l3.15 3.1a2 2 0 0 1 .6 1.45v10.35a2 2 0 0 1-2 2h-9.5a2 2 0 0 1-2-2V5.25a2 2 0 0 1 2-2z')), ('d', P('M9 12.5h6M9 16h3.5'))],
 'setup':    [('o', P('M3.75 7.5h7.25M16 7.5h4.25M3.75 16.5h3.25M12 16.5h8.25')), ('b', C(13.5, 7.5, 2.5)), ('b', C(9.5, 16.5, 2.5))],
}
W = 1.5
SOLID = lambda x: f'<g fill="currentColor" stroke="none">{x}</g>'
SOFT = lambda x: f'<g opacity=".45">{x}</g>'

def outline(parts):
    out = ''
    for k, e in parts:
        out += SOFT(e) if k in ('s', 'ds') else SOLID(e) if k in ('p', 'dp', 'dc') else e
    return out

def filled(parts, mid):
    if not any(k == 'b' for k, _ in parts): return outline(parts)
    cut = ''.join(e for k, e in parts if k in ('d', 'ds'))
    hole = ''.join(e for k, e in parts if k in ('dp', 'dh'))
    exact = ''.join(e for k, e in parts if k == 'dc')
    mask = (f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="24" height="24"><rect width="24" height="24" fill="#fff" stroke="none"/>'
            f'<g fill="none" stroke="#000">{cut}</g><g fill="#000" stroke="#000">{hole}</g>' + (f'<g fill="#000" stroke="none">{exact}</g>' if exact else '') + '</mask>') if cut or hole or exact else ''
    body = ''.join(e for k, e in parts if k == 'b')
    m = f' mask="url(#{mid})"' if mask else ''
    out = mask + f'<g fill="currentColor"{m}>{body}</g>'
    for k, e in parts:
        if k == 'o': out += e
        elif k == 's': out += SOFT(e)
        elif k == 'p': out += SOLID(e)
    return out

HEAD = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{W}" stroke-linecap="round" stroke-linejoin="round">'
_n = [0]
def ic(name, fill=False, style=''):
    _n[0] += 1
    inner = filled(ICONS[name], f'icm{_n[0]}') if fill else outline(ICONS[name])
    st = f' style="{style}"' if style else ''
    return f'<svg class="ic" viewBox="0 0 24 24" aria-hidden="true"{st}>{inner}</svg>'

def CHAPTER():
    T = lambda n, f=False, s='': ic(n, f, s)
    return f'''  <section class="chapter" id="icons" data-title="Icons">
    <div class="topic" id="icons-overview" data-title="Overview">
      <p class="lede">A set drawn for racing: laps, sectors, traces and kit instead of generic app symbols. The drawing follows the conventions people already know from their phone: an even, fine line, simple geometric shapes, and a solid version of each icon for the selected state.</p>
      <div class="orb-tabs" id="icMode" role="group" aria-label="Icon version" style="margin:0 0 16px;width:fit-content"><button type="button" data-m="o" aria-pressed="true">Outline</button><button type="button" data-m="f" aria-pressed="false">Filled</button></div>
      <div class="ic-grid" id="icGrid"></div>
      <p class="cap"><span>24 icons · select one to copy its SVG</span><span>Files in assets/icons</span></p>
    </div>

    <div class="topic" id="icons-construction" data-title="Construction">
      <p class="lede">All icons are drawn on the same 24-unit grid with the same line, so any two sit comfortably side by side.</p>
      <div class="cards two">
        <div class="tile"><div class="stage on-ink"><div class="ic-build">{T('helmet')}</div></div><p class="cap"><span>Outline</span><span>1.5 line</span></p></div>
        <div class="tile"><div class="stage on-ink"><div class="ic-build">{T('helmet', True)}</div></div><p class="cap"><span>Filled</span><span>Details cut out</span></p></div>
      </div>
      <dl class="rules">
        <dt>Grid</dt><dd>24 × 24 units. The drawing stays inside the dashed 20-unit area. Round icons are 17.5 units across; boxy ones are slightly smaller so they look the same size.</dd>
        <dt>Line</dt><dd>1.5 units wide, with round ends and round corners.</dd>
        <dt>Shapes</dt><dd>Built from circles, straight lines and generous corner radii. One clear object per icon, seen flat from the side, front or above.</dd>
        <dt>Two layers</dt><dd>Main lines at full strength; supporting detail, like a tread, a baseline or the other two sectors, at 45%. It gives depth without adding weight.</dd>
        <dt>Filled version</dt><dd>The body of the icon becomes solid and its inner details are cut out of it. Icons made only of open lines, such as telemetry or gears, have no filled version and stay as they are.</dd>
        <dt>New icons</dt><dd>Add the drawing to <code>tools/build_icons.py</code> and run it. The outline, the filled version, the files and this chapter are all generated from that one description.</dd>
      </dl>
    </div>

    <div class="topic" id="icons-size-and-colour" data-title="Size and Colour">
      <p class="lede">Icons take the colour of the text beside them. Outline is the resting state; filled means selected.</p>
      <div class="stage on-ink sm"><div class="ic-sizes" style="color:var(--moon)">
        <figure>{T('wheel', False, 'width:48px;height:48px;stroke-width:1.3')}<span>48</span></figure>
        <figure>{T('wheel', False, 'width:32px;height:32px')}<span>32</span></figure>
        <figure>{T('wheel')}<span>24</span></figure>
        <figure>{T('wheel', False, 'width:20px;height:20px;stroke-width:1.65')}<span>20</span></figure>
        <figure>{T('wheel', False, 'width:16px;height:16px;stroke-width:1.85')}<span>16 MIN</span></figure>
      </div></div>
      <div class="cards two" style="margin-top:12px">
        <div class="tile"><div class="stage on-ink sm" style="color:var(--moon)">{T('timer', False, 'width:48px;height:48px')}</div><p class="cap"><span>Outline, moon</span><span>Default</span></p></div>
        <div class="tile"><div class="stage on-white sm">{T('timer', True, 'width:48px;height:48px')}</div><p class="cap"><span>Filled, void on moon</span><span>Selected</span></p></div>
        <div class="tile"><div class="stage on-ink sm" style="color:var(--haze)">{T('timer', False, 'width:48px;height:48px')}</div><p class="cap"><span>Outline, haze</span><span>Inactive</span></p></div>
        <div class="tile"><div class="stage on-ink sm" style="color:var(--moon);--dot:var(--sun)">{T('live', False, 'width:48px;height:48px')}</div><p class="cap"><span>Sun dot</span><span>Live right now</span></p></div>
      </div>
      <dl class="rules">
        <dt>Sizes</dt><dd>24px as standard, 20px beside small text, 32 and 48px for empty states and headers. 16px is the minimum.</dd>
        <dt>Line weight</dt><dd>The line stays close to 1.5px on screen: slightly lighter in the drawing at 48px, slightly heavier at 20 and 16px.</dd>
        <dt>Outline or filled</dt><dd>Outline everywhere by default. Filled only for the selected item in navigation and for the icon on the one electric button.</dd>
        <dt>Colour</dt><dd>Moon by default, haze when inactive, void on a white pill when selected, white on electric. Never a gradient and never nova.</dd>
        <dt>Sun dot</dt><dd>The centre of the live icon may turn sun yellow while a session is running. This is the tiny status dot the Color chapter allows, and the only colour inside an icon.</dd>
        <dt>With text</dt><dd>Icon to the left, 10 to 14px gap, centred on the text. An icon without a label needs a tooltip or an accessible name.</dd>
      </dl>
    </div>

    <div class="topic" id="icons-in-use" data-title="In Use">
      <p class="lede">The same three patterns as the rest of the system: a pill of round buttons for navigation, quiet rows for data, and one blue action.</p>
      <div class="cards cols">
        <div class="tile"><div class="stage on-ink"><div class="ic-nav"><span class="go">{T('flag', True)}</span><span class="on">{T('lap', True)}</span><span>{T('telemetry')}</span><span>{T('onboard')}</span><span>{T('standings')}</span><span>{T('helmet')}</span></div></div><p class="cap"><span>Navigation pill</span><span>Selected item filled</span></p></div>
        <div class="tile"><div class="stage on-ink"><div class="ic-rows"><div>{T('timer')}<b>Best lap</b><em>Example</em></div><div>{T('speed')}<b>Top speed</b><em>Example</em></div><div>{T('tyre')}<b>Tyre set</b><em>Example</em></div><div style="--dot:var(--sun)">{T('live')}<b>Session</b><em>Live</em></div></div></div><p class="cap"><span>Data rows</span><span>24px outline, label, value</span></p></div>
        <div class="tile"><div class="stage haze"><span class="ic-pill">{T('coach', False, 'width:20px;height:20px;stroke-width:1.65')}Ask the coach</span></div><p class="cap"><span>White pill</span><span>20px icon with a label</span></p></div>
      </div>
    </div>

    <div class="topic" id="icons-what-to-avoid" data-title="What to Avoid">
      <p class="lede">The set only works if every icon looks drawn by the same hand.</p>
      <div class="cards cols">
        <div class="card dont"><div class="label"><span>✕ Changing the line</span></div><div class="body" style="justify-items:center">{T('wheel', False, 'width:56px;height:56px;stroke-width:3.2')}</div><p class="note">Keep 1.5. No bold or hairline versions.</p></div>
        <div class="card dont"><div class="label"><span>✕ Square ends</span></div><div class="body" style="justify-items:center">{T('gears', False, 'width:56px;height:56px;stroke-linecap:butt;stroke-linejoin:miter')}</div><p class="note">Ends and corners are always round.</p></div>
        <div class="card dont"><div class="label"><span>✕ Homemade fills</span></div><div class="body" style="justify-items:center"><svg class="ic" viewBox="0 0 24 24" style="width:56px;height:56px;fill:currentColor">{''.join(e for k, e in ICONS['timer'])}</svg></div><p class="note">Use the supplied filled file; it keeps the details.</p></div>
        <div class="card dont"><div class="label"><span>✕ Colouring the icon</span></div><div class="body" style="justify-items:center;color:var(--nova)">{T('flag', False, 'width:56px;height:56px')}</div><p class="note">Icons follow the text colour.</p></div>
        <div class="card dont"><div class="label"><span>✕ Filled everywhere</span></div><div class="body" style="justify-items:center"><div style="display:flex;gap:14px">{T('lap', True, 'width:36px;height:36px')}{T('helmet', True, 'width:36px;height:36px')}{T('coach', True, 'width:36px;height:36px')}</div></div><p class="note">Filled means selected. One per group.</p></div>
        <div class="card dont"><div class="label"><span>✕ Mixing icon sets</span></div><div class="body" style="justify-items:center"><div style="display:flex;gap:18px;align-items:center">{T('timer', False, 'width:44px;height:44px')}<svg viewBox="0 0 24 24" style="width:44px;height:44px" fill="currentColor"><path d="M12 2l2.4 7.2H22l-6 4.5 2.3 7.3-6.3-4.6L5.7 21 8 13.7 2 9.2h7.6z"/></svg></div></div><p class="note">No emoji, stock icons or other libraries beside these.</p></div>
      </div>
    </div>
  </section>
'''

JS = lambda data: '''  const ICONS = ''' + data + ''';
  const icGrid = document.getElementById('icGrid'), icMode = document.getElementById('icMode');
  let icM = 'o';
  const drawIcons = () => icGrid.innerHTML = Object.keys(ICONS).map(n => `<button type="button" class="ic-cell" data-ic="${n}" aria-label="Copy the ${n} icon"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true">${ICONS[n][icM]}</svg><span>${n}</span></button>`).join('');
  drawIcons();
  icMode.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    icM = b.dataset.m;
    icMode.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b));
    drawIcons();
  });
  icGrid.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    const svg = `''' + HEAD.replace('`', '') + '''${ICONS[b.dataset.ic][icM].replace(' class="dot"', '')}</svg>`;
    const label = b.querySelector('span'), done = () => { label.textContent = 'Copied'; setTimeout(() => label.textContent = b.dataset.ic, 1200); };
    navigator.clipboard ? navigator.clipboard.writeText(svg).then(done, done) : done();
  });
'''

def main():
    d = os.path.join(ROOT, 'assets', 'icons'); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.svg'): os.remove(os.path.join(d, f))
    data = {}
    for n, parts in ICONS.items():
        o, f = outline(parts), filled(parts, f'icg-{n}')
        data[n] = {'o': o, 'f': f}
        open(os.path.join(d, n + '.svg'), 'w').write(HEAD + o.replace(' class="dot"', '') + '</svg>\n')
        if any(k == 'b' for k, _ in parts):
            open(os.path.join(d, n + '.fill.svg'), 'w').write(HEAD + filled(parts, 'm').replace(' class="dot"', '') + '</svg>\n')
    p = os.path.join(ROOT, 'index.html'); s = open(p).read()
    for a, b, new in (('  <!-- ICONS:START -->\n', '  <!-- ICONS:END -->\n', CHAPTER()), ('  // ICONS:START\n', '  // ICONS:END\n', JS(json.dumps(data)))):
        i, j = s.index(a) + len(a), s.index(b)
        s = s[:i] + new + s[j:]
    open(p, 'w').write(s)
    print(len(ICONS), 'icons,', len(os.listdir(d)), 'files')

if __name__ == '__main__': main()

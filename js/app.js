(function () {
  'use strict';
  const C = window.Chart, T = window.Tools, $ = id => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  function el(n, a, t) { const e = document.createElementNS(NS, n); for (const k in a) if (a[k] != null) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; return e; }
  const COLORS = ['#123a6b', '#8a5a00', '#1f7a3d', '#8a2f1f', '#0f6a78', '#5a3d8a'];

  /* ---------- STEP1 アニメーション ---------- */
  const USERS = 3, SIZE = 4;
  let tick = 0, timer = null;

  /** 回線交換：1人ずつ順番に、その人のぶんを連続して送る */
  function circuitSchedule(users, size) {
    const s = [];
    for (let u = 0; u < users; u++) for (let k = 0; k < size; k++) s.push(u);
    return s;
  }
  /** パケット交換：順番に1コマずつ交代で送る */
  function packetSchedule(users, size) {
    const s = [];
    for (let k = 0; k < size; k++) for (let u = 0; u < users; u++) s.push(u);
    return s;
  }
  function finishTimes(sched, users, size) {
    const done = new Array(users).fill(0), cnt = new Array(users).fill(0);
    sched.forEach((u, i) => { cnt[u]++; if (cnt[u] === size) done[u] = i + 1; });
    return done;
  }

  function drawAnim() {
    const cs = circuitSchedule(USERS, SIZE), ps = packetSchedule(USERS, SIZE);
    const total = cs.length;
    const W = 660, H = 300;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img', 'aria-label': '2つの通信方式の比較' });
    const rowY = [90, 210];
    ['回線交換方式', 'パケット交換方式'].forEach((name, r) => {
      const y = rowY[r];
      svg.appendChild(el('text', { x: 10, y: y - 40, class: 'tlab', 'font-weight': 700 }, name));
      svg.appendChild(el('line', { x1: 110, y1: y, x2: W - 110, y2: y, class: 'wire' }));
      // 送信側・受信側
      [[70, '送信側'], [W - 70, '受信側']].forEach(([x, lb]) => {
        svg.appendChild(el('rect', { x: x - 40, y: y - 26, width: 80, height: 52, class: 'node' }));
        svg.appendChild(el('text', { x: x, y: y + 4, class: 'nlab' }, lb));
      });
      const sched = r === 0 ? cs : ps;
      const shown = sched.slice(0, tick);
      const x0 = 118, x1 = W - 118;
      shown.forEach((u, i) => {
        const p = (tick - i) / Math.max(1, total);
        const x = x0 + Math.min(1, (tick - i) / 6) * (x1 - x0);
        if (tick - i > 6) return;
        svg.appendChild(el('rect', { x: x - 12, y: y - 9, width: 24, height: 18, rx: 3,
          fill: COLORS[u % COLORS.length], class: 'pk' }));
      });
      // 進捗バー
      const done = finishTimes(sched, USERS, SIZE);
      for (let u = 0; u < USERS; u++) {
        const bx = 118 + u * 92, by = y + 32;
        svg.appendChild(el('rect', { x: bx, y: by, width: 80, height: 12, fill: '#ebe8e2' }));
        const c = shown.filter(v => v === u).length;
        svg.appendChild(el('rect', { x: bx, y: by, width: 80 * c / SIZE, height: 12, fill: COLORS[u % COLORS.length] }));
        svg.appendChild(el('text', { x: bx + 40, y: by + 26, class: 'tlab', 'text-anchor': 'middle', 'font-size': 10 },
          (c >= SIZE ? '完了 ' + done[u] : c + '/' + SIZE)));
      }
    });
    const box = $('animBox'); box.innerHTML = ''; box.appendChild(svg);
    $('tick').textContent = '経過 ' + tick;
    const cd = finishTimes(cs, USERS, SIZE), pd = finishTimes(ps, USERS, SIZE);
    $('mCirc').textContent = cs.length;
    $('mPack').textContent = ps.length;
    $('legend').innerHTML = Array.from({ length: USERS }, (_, u) =>
      '<span class="u"><i style="background:' + COLORS[u] + '"></i>' + (u + 1) + '人目（完了：回線 ' + cd[u] + ' / パケット ' + pd[u] + '）</span>').join('');
    const n = $('animNote');
    n.className = 'note info';
    n.innerHTML = '<strong>全員が終わる時間は同じ ' + cs.length + ' コマ</strong>ですが、途中がちがいます。<br>' +
      '回線交換方式では1人目が最初に完了し（' + cd[0] + 'コマ）、3人目は最後まで待たされます（' + cd[2] + 'コマ）。<br>' +
      'パケット交換方式では<strong>全員がほぼ同時に少しずつ進み</strong>、完了は ' + pd[0] + '〜' + pd[2] + 'コマ。' +
      '待たされている間も回線が空いていれば他の人が使えるのが、パケット交換方式の効率のよさです。';
  }
  function play() {
    if (timer) { clearInterval(timer); timer = null; $('play').textContent = '▶ 動かす'; return; }
    $('play').textContent = '⏸ 止める';
    timer = setInterval(() => {
      tick++;
      if (tick > USERS * SIZE + 6) { tick = 0; }
      drawAnim();
    }, 420);
  }

  /* ---------- STEP2 利用者数 ---------- */
  function drawSim() {
    const n = +$('nUsers').value, size = +$('dataSize').value, idle = +$('idle').value / 100;
    $('nUsersV').textContent = n; $('dataSizeV').textContent = size; $('idleV').textContent = Math.round(idle * 100);
    // 回線交換：1人が占有する時間は「データ量 ÷ (1 − 待ち割合)」
    const hold = Math.ceil(size / Math.max(0.05, 1 - idle));
    const cTime = n * hold;
    // パケット交換：実データだけを詰めて送る
    const pTime = n * size;
    $('cTime').textContent = cTime;
    $('pTime').textContent = pTime;
    $('cUse').textContent = Math.round(n * size / cTime * 100);
    $('pUse').textContent = 100;
    C.bar($('cmpChart'), { W: 700, H: 260,
      labels: ['回線交換方式', 'パケット交換方式'], values: [cTime, pTime],
      colors: ['#858a92', '#123a6b'], unit: 'コマ', yMin: 0 });
    const nt = $('simNote');
    nt.className = cTime > pTime * 1.4 ? 'note ok' : 'note info';
    nt.innerHTML = '回線交換方式では、送るものが無い時間も回線をおさえるので <strong>' + cTime +
      ' コマ</strong>かかります。パケット交換方式は実際のデータだけを詰めて送るので <strong>' + pTime + ' コマ</strong>。<br>' +
      (idle > 0
        ? '待ち時間の割合が ' + Math.round(idle * 100) + '％あるため、回線交換方式では回線の <strong>' +
          (100 - Math.round(n * size / cTime * 100)) + '％がむだ</strong>になっています。'
        : '待ち時間が0％なら両方式の所要時間は同じです。<strong>待ち時間の割合を上げてみてください。</strong>');
  }

  /* ---------- STEP4 判定 ---------- */
  const QUIZ = [
    { t: 'データを小さい単位に分割して、個別に伝送する。', a: 'パケット交換方式',
      why: 'これがパケット交換方式の定義そのものです。分割された1つ1つをパケットといいます。' },
    { t: '通信経路が一度確立されると、安定した通信が行える。', a: '回線交換方式',
      why: '回線を占有するため、通信速度が安定します。パケット交換方式では混雑の影響を受けます。' },
    { t: '回線を占有している間は他の利用者が同じ回線を利用することができない。', a: '回線交換方式',
      why: '占有するのが回線交換方式の特徴です。効率は悪くなります。' },
    { t: '通信速度が保障され安定した通信が行える一方で、コストが高くなる可能性がある。', a: '回線交換方式',
      why: '回線を独り占めするため、そのぶん費用がかかります。' },
    { t: '通信速度は保障されないが、同時に複数人が同じ回線を利用することができる。', a: 'パケット交換方式',
      why: 'パケット交換方式の長所と短所を両方述べた記述です。インターネットがこの方式です。' },
    { t: '1つの回線に異なる宛先のパケットが混在してもよい。', a: 'パケット交換方式',
      why: 'パケットには宛先の情報がついているので、混ざっても正しく届きます。' },
    { t: '従来の固定電話で用いられていた。', a: '回線交換方式',
      why: '電話は通話中ずっと回線をつないだままにする方式でした。' },
    { t: '回線を効率的に利用して、回線数より多くのユーザが同時に通信できる。', a: 'パケット交換方式',
      why: '本文の【ウ】の答えにあたる、パケット交換方式のいちばんの長所です。' },
    { t: '通信中は回線を占有できるため、時間あたりに通信できるデータ量が安定する。', a: '回線交換方式',
      why: '本文の【イ】の答えにあたる、回線交換方式の長所です。' }
  ];
  let qList = [], qi = 0, qScore = 0;
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  function startQuiz() { qList = shuffle(QUIZ); qi = 0; qScore = 0; renderQ(); }
  function renderQ() {
    if (qi >= qList.length) {
      $('qText').textContent = qScore + ' / ' + qList.length + ' 問正解';
      $('qChoices').innerHTML = ''; $('qFb').hidden = true; $('qNext').disabled = true;
      $('qProgress').textContent = qList.length + ' / ' + qList.length; return;
    }
    const it = qList[qi];
    $('qProgress').textContent = (qi + 1) + ' / ' + qList.length;
    $('qScore').textContent = qScore;
    $('qText').textContent = it.t;
    const box = $('qChoices'); box.className = 'choice4'; box.innerHTML = '';
    ['回線交換方式', 'パケット交換方式'].forEach(c => {
      const b = document.createElement('button');
      b.className = 'btn'; b.textContent = c; b.dataset.c = c;
      b.style.textAlign = 'center';
      b.addEventListener('click', () => answerQ(c));
      box.appendChild(b);
    });
    $('qFb').hidden = true; $('qNext').disabled = true;
    $('qNext').textContent = (qi === qList.length - 1) ? '結果を見る' : '次の問題';
  }
  function answerQ(c) {
    const it = qList[qi], ok = c === it.a, box = $('qChoices');
    box.classList.add('locked');
    [...box.children].forEach(b => {
      if (b.dataset.c === it.a) b.classList.add('correct');
      else if (b.dataset.c === c) b.classList.add('wrong');
    });
    if (ok) qScore++;
    const fb = $('qFb');
    fb.className = 'note ' + (ok ? 'ok' : 'ng');
    fb.innerHTML = (ok ? '正解。' : '正解は「<strong>' + it.a + '</strong>」。') + it.why;
    fb.hidden = false;
    $('qScore').textContent = qScore; $('qNext').disabled = false;
  }

  function init() {
    $('play').addEventListener('click', play);
    $('step1btn').addEventListener('click', () => { tick++; drawAnim(); });
    $('resetAnim').addEventListener('click', () => { tick = 0; drawAnim(); });
    ['nUsers', 'dataSize', 'idle'].forEach(i => $(i).addEventListener('input', drawSim));
    $('qNext').addEventListener('click', () => { qi++; renderQ(); });
    $('qReset').addEventListener('click', startQuiz);
    window.Terms.glossary($('glossBox'), ['回線交換方式', 'パケット交換方式', 'パケット', 'プロトコル', 'LAN', 'ビット毎秒']);
    tick = 6; drawAnim(); drawSim(); startQuiz();
    window.Terms.attach();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();

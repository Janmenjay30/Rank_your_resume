const form = document.getElementById('rankForm');
const jdEl = document.getElementById('jd');
const resume1El = document.getElementById('resume1');
const resume2El = document.getElementById('resume2');
const resume3El = document.getElementById('resume3');
const resume4El = document.getElementById('resume4');
const submitBtn = document.getElementById('submitBtn');
const clearBtn = document.getElementById('clearBtn');
const statusEl = document.getElementById('status');
const resultsBody = document.getElementById('resultsBody');

function setStatus(message, kind = 'info') {
  statusEl.textContent = message;
  statusEl.classList.toggle('error', kind === 'error');
}

function setLoading(isLoading) {
  submitBtn.disabled = isLoading;
  submitBtn.textContent = isLoading ? 'Ranking…' : 'Rank resumes';
}

function renderResults(rankings) {
  resultsBody.innerHTML = '';

  if (!rankings || rankings.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 3;
    td.className = 'muted';
    td.textContent = 'No results.';
    tr.appendChild(td);
    resultsBody.appendChild(tr);
    return;
  }

  rankings.forEach((r, idx) => {
    const tr = document.createElement('tr');

    const tdIdx = document.createElement('td');
    tdIdx.textContent = String(idx + 1);

    const tdName = document.createElement('td');
    tdName.textContent = r.resume;

    const tdScore = document.createElement('td');
    tdScore.className = 'num';
    tdScore.textContent = typeof r.score === 'number' ? r.score.toFixed(4) : String(r.score);

    tr.appendChild(tdIdx);
    tr.appendChild(tdName);
    tr.appendChild(tdScore);
    resultsBody.appendChild(tr);
  });
}

function getSelectedResumeFiles() {
  const pickers = [resume1El, resume2El, resume3El, resume4El];
  const files = [];
  for (const el of pickers) {
    if (el?.files && el.files.length > 0) files.push(el.files[0]);
  }
  return files;
}

function describeSelectedFiles() {
  const files = getSelectedResumeFiles();
  if (files.length === 0) return 'No resumes selected.';
  const names = files.map((f) => f.name).join(', ');
  return `Selected ${files.length}/4: ${names}`;
}

[resume1El, resume2El, resume3El, resume4El].forEach((el) => {
  el?.addEventListener('change', () => setStatus(describeSelectedFiles()));
});

clearBtn.addEventListener('click', () => {
  jdEl.value = '';
  resume1El.value = '';
  resume2El.value = '';
  resume3El.value = '';
  resume4El.value = '';
  renderResults([]);
  setStatus('Cleared.');
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const jd = jdEl.value.trim();
  const files = getSelectedResumeFiles();

  if (!jd) {
    setStatus('Please paste a job description.', 'error');
    return;
  }
  if (!files || files.length === 0) {
    setStatus('Please select at least 1 resume (PDF).', 'error');
    return;
  }
  if (files.length > 4) {
    setStatus('Please select at most 4 resumes.', 'error');
    return;
  }

  const fd = new FormData();
  fd.append('jd', jd);
  for (const f of files) {
    // Repeat the same field name to send multiple files.
    fd.append('resumes', f, f.name);
  }

  try {
    setLoading(true);
    setStatus(`Uploading ${files.length} file(s)…`);

    const resp = await fetch('/api/rank', {
      method: 'POST',
      body: fd,
    });

    if (!resp.ok) {
      let msg = `Request failed: ${resp.status}`;
      try {
        const data = await resp.json();
        msg = data?.detail ? String(data.detail) : JSON.stringify(data);
      } catch {
        const text = await resp.text();
        if (text) msg = text;
      }
      throw new Error(msg);
    }

    const data = await resp.json();
    renderResults(data.rankings);
    setStatus(`Done. Ranked ${data.rankings?.length ?? 0} resume(s).`);
  } catch (err) {
    renderResults([]);
    setStatus(err?.message || String(err), 'error');
  } finally {
    setLoading(false);
  }
});

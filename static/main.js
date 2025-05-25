
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('createRecordForm');
  const nameInput = form.elements['name'];

  // reset input when modal is shown
  const modalEl = document.getElementById('createRecordModal');
  modalEl.addEventListener('shown.bs.modal', () => {
    nameInput.value = '';
    nameInput.focus();
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = nameInput.value.trim();
    if (!name) return;
    const color = NORD_COLORS[Math.floor(Math.random()*NORD_COLORS.length)];
    const res = await fetch('/api/records', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, color})
    });
    if (res.ok) {
      location.reload();
    } else {
      alert('Error al crear registro');
    }
  });

  // handle start buttons
  document.querySelectorAll('[data-action="start"]')?.forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      const recordId = btn.dataset.recordId;
      const res = await fetch(`/api/records/${recordId}/start`, {method:'POST'});
      if(res.ok){
        location.reload();
      }
    });
  });

  // handle stop buttons
  document.querySelectorAll('[data-action="stop"]')?.forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      const entryId = btn.dataset.entryId;
      if(!confirm('¿Desea finalizar este registro?')) return;
      const res = await fetch(`/api/entries/${entryId}/stop`, {method:'POST'});
      if(res.ok){
        location.reload();
      }
    });
  });
});

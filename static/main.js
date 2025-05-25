
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('createRecordForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = form.elements['name'].value.trim();
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
});

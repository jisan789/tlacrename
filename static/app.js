// Account Name UI logic

document.addEventListener('DOMContentLoaded', () => {
  loadAccountName();

  const form = document.getElementById('update-name-form');
  const input = document.getElementById('new-name-input');
  const btn = document.getElementById('submit-btn');
  const statusMsg = document.getElementById('status-message');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const newName = input.value.trim();
    if (!newName) return;

    btn.disabled = true;
    btn.textContent = 'Updating...';
    hideStatus();

    try {
      const res = await fetch('/name', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to update name');
      }

      document.getElementById('account-name').textContent = data.name;
      input.value = '';
      showStatus('Account name updated successfully!', 'success');
    } catch (err) {
      showStatus(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Change Name';
    }
  });
});

async function loadAccountName() {
  const nameEl = document.getElementById('account-name');
  try {
    const res = await fetch('/name');
    if (!res.ok) throw new Error('Failed to fetch name');
    const data = await res.json();
    nameEl.textContent = data.name || 'No Name Set';
  } catch (err) {
    nameEl.textContent = 'Error Loading Name';
    showStatus(err.message, 'error');
  }
}

function showStatus(msg, type) {
  const el = document.getElementById('status-message');
  el.textContent = msg;
  el.className = `status-msg ${type}`;
  setTimeout(() => {
    hideStatus();
  }, 4000);
}

function hideStatus() {
  const el = document.getElementById('status-message');
  el.className = 'status-msg hidden';
}

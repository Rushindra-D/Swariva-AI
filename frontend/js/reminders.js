/**
 * SWARIVA AI — Daily Reminders & Medicine Assistant
 * Manages daily routine, medicine, and appointment reminders.
 * Supports spoken audio reminders via Gnani Timbre.
 */

document.addEventListener('DOMContentLoaded', () => {
  const reminderForm = document.getElementById('reminder-form');
  const titleInput = document.getElementById('reminder-title');
  const timeInput = document.getElementById('reminder-time');
  const categorySelect = document.getElementById('reminder-category');
  const notesInput = document.getElementById('reminder-notes');
  const reminderList = document.getElementById('reminder-list');
  const emptyState = document.getElementById('reminders-empty-state');

  // Load reminders from localStorage
  function getReminders() {
    const raw = localStorage.getItem(CONFIG.STORAGE_KEYS.REMINDERS);
    if (!raw) {
      // Default sample reminders
      const defaults = [
        {
          id: 'rem_1',
          title: 'Blood Pressure Medicine',
          time: '08:00',
          category: 'medicine',
          notes: 'Take 1 tablet with water after breakfast.',
          completed: false,
        },
        {
          id: 'rem_2',
          title: 'Evening Walk & Hydration',
          time: '17:30',
          category: 'routine',
          notes: 'Gentle 20-minute walk in the garden.',
          completed: false,
        },
      ];
      localStorage.setItem(CONFIG.STORAGE_KEYS.REMINDERS, JSON.stringify(defaults));
      return defaults;
    }
    try {
      return JSON.parse(raw);
    } catch {
      return [];
    }
  }

  function saveReminders(items) {
    localStorage.setItem(CONFIG.STORAGE_KEYS.REMINDERS, JSON.stringify(items));
    renderReminders();
  }

  function renderReminders() {
    const items = getReminders();
    if (!reminderList) return;

    reminderList.innerHTML = '';

    if (items.length === 0) {
      if (emptyState) emptyState.style.display = 'block';
      return;
    }
    if (emptyState) emptyState.style.display = 'none';

    items.forEach((item) => {
      const card = document.createElement('div');
      card.className = `card reminder-card ${item.completed ? 'completed' : ''}`;
      card.style.display = 'flex';
      card.style.alignItems = 'center';
      card.style.justifyContent = 'space-between';
      card.style.gap = '1rem';
      card.style.padding = '1.25rem';
      card.style.marginBottom = '0.75rem';

      const icon = item.category === 'medicine' ? '💊' : item.category === 'appointment' ? '🩺' : '⏰';

      const details = document.createElement('div');
      details.style.flex = '1';
      details.innerHTML = `
        <div style="display:flex; align-items:center; gap:0.5rem;">
          <span style="font-size:1.3rem;">${icon}</span>
          <h4 style="font-size:1.05rem; text-decoration: ${item.completed ? 'line-through' : 'none'};">${item.title}</h4>
          <span style="font-size:0.8rem; background:rgba(255,255,255,0.08); padding:2px 8px; border-radius:12px; color:var(--accent-cyan);">${item.time}</span>
        </div>
        ${item.notes ? `<p style="font-size:0.86rem; color:var(--text-muted); margin-top:0.35rem;">${item.notes}</p>` : ''}
      `;

      const actions = document.createElement('div');
      actions.style.display = 'flex';
      actions.style.alignItems = 'center';
      actions.style.gap = '0.5rem';

      // Read Aloud / Speak button
      const speakBtn = document.createElement('button');
      speakBtn.className = 'btn btn-secondary';
      speakBtn.style.padding = '0.45rem 0.8rem';
      speakBtn.style.fontSize = '0.85rem';
      speakBtn.innerHTML = '🔊 Speak';
      speakBtn.title = 'Hear this reminder via Gnani Timbre';
      speakBtn.onclick = async () => {
        showToast('Generating reminder voice announcement...', 'info');
        const textToSpeak = `Reminder for ${item.title} at ${item.time}. ${item.notes || ''}`;
        try {
          const res = await SwarivaAPI.speakText({ text: textToSpeak });
          if (res.success && res.audio_base64) {
            audioController.playBase64(res.audio_base64);
          }
        } catch (err) {
          showToast(err.message, 'error');
        }
      };

      // Toggle Complete Button
      const toggleBtn = document.createElement('button');
      toggleBtn.className = item.completed ? 'btn btn-secondary' : 'btn btn-primary';
      toggleBtn.style.padding = '0.45rem 0.8rem';
      toggleBtn.style.fontSize = '0.85rem';
      toggleBtn.textContent = item.completed ? 'Undo' : 'Done';
      toggleBtn.onclick = () => {
        item.completed = !item.completed;
        saveReminders(items);
      };

      // Delete Button
      const delBtn = document.createElement('button');
      delBtn.className = 'btn btn-danger';
      delBtn.style.padding = '0.45rem 0.8rem';
      delBtn.style.fontSize = '0.85rem';
      delBtn.textContent = '✕';
      delBtn.title = 'Delete reminder';
      delBtn.onclick = () => {
        const filtered = items.filter((r) => r.id !== item.id);
        saveReminders(filtered);
        showToast('Reminder deleted', 'info');
      };

      actions.appendChild(speakBtn);
      actions.appendChild(toggleBtn);
      actions.appendChild(delBtn);

      card.appendChild(details);
      card.appendChild(actions);
      reminderList.appendChild(card);
    });
  }

  if (reminderForm) {
    reminderForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const title = titleInput.value.trim();
      const time = timeInput.value.trim();
      if (!title || !time) {
        showToast('Please fill in title and time.', 'error');
        return;
      }

      const newReminder = {
        id: 'rem_' + Date.now(),
        title,
        time,
        category: categorySelect ? categorySelect.value : 'routine',
        notes: notesInput ? notesInput.value.trim() : '',
        completed: false,
      };

      const items = getReminders();
      items.push(newReminder);
      saveReminders(items);

      titleInput.value = '';
      timeInput.value = '';
      if (notesInput) notesInput.value = '';

      showToast('Reminder added successfully!', 'success');
    });
  }

  renderReminders();
});

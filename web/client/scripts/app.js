'use strict';

function render() {
  renderTopbar();
  renderSidebar();
  const isCalendar = state.view === 'calendar';
  const frame = document.getElementById('calendar-frame');
  const main = document.getElementById('main');
  frame.style.display = isCalendar && state.calendarUrl ? 'block' : 'none';
  main.style.display = isCalendar && state.calendarUrl ? 'none' : '';
  if (isCalendar) { renderCalendarView(); return; }
  if (state.view === 'daysheet') { renderDaysheetView(); return; }
  if (!state.data) return;
  if (state.selectedList) renderFocusedView(state.selectedList);
  else renderCardsView();
}

(async () => {
  const cfg = await api('GET', API.config);
  if (cfg) {
    state.calendarUrl = cfg.calendarUrl || '';
    if (state.calendarUrl) {
      document.getElementById('calendar-frame').src = state.calendarUrl;
    }
  }
  await refresh();
})();

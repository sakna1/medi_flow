// Add task to the to-do list
function addTask() {
  const input = document.getElementById('new-task');
  const task = input.value.trim();
  if (task === '') return;

  const list = document.getElementById('todo-list');
  const li = document.createElement('li');
  li.innerHTML = `<input type="checkbox"> ${task}`;
  list.appendChild(li);

  input.value = '';
}

 const openBtn = document.getElementById('openFormBtn');
    const popupBox = document.getElementById('popupBox');
    const popupOverlay = document.getElementById('popupOverlay');

    openBtn.addEventListener('click', function(e) {
      e.preventDefault();
      popupBox.classList.add('active');
      popupOverlay.style.display = 'block';
    });

    popupOverlay.addEventListener('click', function() {
      popupBox.classList.remove('active');
      popupOverlay.style.display = 'none';
    });
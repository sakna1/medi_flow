// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.querySelector('.notification-search input');
  const notifications = document.querySelectorAll('.notification-item');

  searchInput.addEventListener('input', function() {
    const query = this.value.toLowerCase();

    notifications.forEach(function(item) {
      const text = item.textContent.toLowerCase();
      if (text.includes(query)) {
        item.style.display = 'block';
      } else {
        item.style.display = 'none';
      }
    });
  });
});


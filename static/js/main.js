/**
 * main.js - Client-Side Enhancements for Smart Parking Management System
 * Handles sidebar toggling, alert dismissal, and modal/confirmation actions.
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Sidebar Toggle
  const sidebar = document.getElementById('sidebar');
  const mobileToggle = document.getElementById('mobileMenuToggle');
  const sidebarClose = document.getElementById('sidebarClose');

  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });
  }

  if (sidebarClose && sidebar) {
    sidebarClose.addEventListener('click', function () {
      sidebar.classList.remove('show');
    });
  }

  // Close sidebar on click outside on small screens
  document.addEventListener('click', function (event) {
    if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('show')) {
      if (!sidebar.contains(event.target) && (!mobileToggle || !mobileToggle.contains(event.target))) {
        sidebar.classList.remove('show');
      }
    }
  });

  // 2. Alert Dismissal
  const alertCloseBtns = document.querySelectorAll('.alert-close');
  alertCloseBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const alert = this.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        alert.style.transition = 'all 0.3s ease';
        setTimeout(function () {
          alert.remove();
        }, 300);
      }
    });
  });

  // 3. Vehicle Type Radio Card Selection Visual State
  const radioCards = document.querySelectorAll('.radio-card');
  radioCards.forEach(function (card) {
    const radio = card.querySelector('input[type="radio"]');
    if (radio) {
      if (radio.checked) {
        card.classList.add('selected');
      }
      radio.addEventListener('change', function () {
        radioCards.forEach(c => c.classList.remove('selected'));
        if (this.checked) {
          card.classList.add('selected');
        }
      });
    }
  });
});

/**
 * Confirm before exiting vehicle
 */
function confirmExit(vehicleNumber, slotNumber, fee) {
  return confirm(
    `Are you sure you want to exit vehicle ${vehicleNumber} from slot ${slotNumber}?\nTotal Fee to collect: ₹${fee}`
  );
}

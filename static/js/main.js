document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const toggleBtn = document.getElementById('sidebar-toggle');
    const dropdowns = document.querySelectorAll('.menu-dropdown');

    // Sidebar Toggle
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            if (window.innerWidth > 768) {
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('full');
            } else {
                sidebar.classList.toggle('open');
            }
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(event.target) && !toggleBtn.contains(event.target) && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
            }
        }
    });

    // Dropdown Logic
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.menu-item');
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Close other dropdowns
            dropdowns.forEach(other => {
                if (other !== dropdown) {
                    other.classList.remove('open');
                }
            });
            
            dropdown.classList.toggle('open');
        });
    });

    // Handle active menu items based on URL
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.sidebar-menu a');
    
    menuItems.forEach(item => {
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
            
            // If it's in a dropdown, open that dropdown
            const parentDropdown = item.closest('.menu-dropdown');
            if (parentDropdown) {
                parentDropdown.classList.add('open');
            }
        }
    });

    // Responsive adjustment on resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('open');
        } else {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('full');
        }
    });
});

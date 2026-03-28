document.addEventListener('DOMContentLoaded', function () {

    // Mobile nav toggle
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function () {
            navLinks.classList.toggle('active');
        });
        document.addEventListener('click', function (e) {
            if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
                navLinks.classList.remove('active');
            }
        });
    }

    // Auto-dismiss flash messages after 5 seconds
    document.querySelectorAll('.flash').forEach(function (flash) {
        setTimeout(function () {
            flash.style.transition = 'opacity 0.3s, transform 0.3s';
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-8px)';
            setTimeout(function () { flash.remove(); }, 300);
        }, 5000);
    });

    // Unread message badge polling (every 30s)
    if (document.querySelector('.badge') || document.querySelector('[data-unread-poll]')) {
        setInterval(function () {
            fetch('/api/messages/unread')
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    var badges = document.querySelectorAll('.nav-link .badge');
                    badges.forEach(function (b) {
                        if (data.unread > 0) {
                            b.textContent = data.unread;
                            b.style.display = '';
                        } else {
                            b.style.display = 'none';
                        }
                    });
                })
                .catch(function () {});
        }, 30000);
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

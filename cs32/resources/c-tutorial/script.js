'use strict';

// Smooth scroll for TOC links
document.addEventListener('DOMContentLoaded', function() {
  const tocLinks = document.querySelectorAll('.table-of-contents a');
  
  // Smooth scroll on click
  tocLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const targetSection = document.querySelector(targetId);
      
      if (targetSection) {
        targetSection.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // Highlight active section on scroll
  function highlightActiveSection() {
    const sections = document.querySelectorAll('section[id], h3[id]');
    const scrollPosition = window.scrollY + 100;

    sections.forEach(section => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.offsetHeight;
      const sectionId = section.getAttribute('id');

      if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
        // Remove active class from all links
        tocLinks.forEach(link => link.classList.remove('active'));
        
        // Add active class to current link
        const activeLink = document.querySelector(`.table-of-contents a[href="#${sectionId}"]`);
        if (activeLink) {
          activeLink.classList.add('active');
        }
      }
    });
  }

  // Run on scroll
  window.addEventListener('scroll', highlightActiveSection);
  
  // Run once on page load
  highlightActiveSection();
});



document.addEventListener('DOMContentLoaded', function(){
    const modal = document.getElementById('callModal');
    if(!modal) return; // нет модалки — выходим тихо
    
    const dialog = modal.querySelector('.modal__dialog');
    const form = modal.querySelector('#callForm');
    const openers = document.querySelectorAll('[data-call-modal-open]');
    const overlay = modal.querySelector('.modal__overlay');
    const closeBtns = modal.querySelectorAll('[data-close]');
    
    function openModal(){
    modal.classList.add('is-open');
    document.body.classList.add('modal-open');
    setTimeout(()=> form?.querySelector('input[name="name"]')?.focus(), 30);
    }
    function closeModal(){
    modal.classList.remove('is-open');
    document.body.classList.remove('modal-open');
    }
    
    openers.forEach(el=>{
    el.addEventListener('click', function(e){ e.preventDefault(); openModal(); });
    });
    overlay?.addEventListener('click', closeModal);
    closeBtns.forEach(b=> b.addEventListener('click', function(e){ e.preventDefault(); closeModal(); }));
    document.addEventListener('keydown', function(e){
    if(e.key === 'Escape' && modal.classList.contains('is-open')) closeModal();
    });
    });
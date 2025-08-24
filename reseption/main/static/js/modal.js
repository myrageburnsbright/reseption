document.addEventListener('DOMContentLoaded', function(){
    const modal = document.getElementById('callModal');
    if(!modal) return; // нет модалки — выходим тихо
    
    const dialog = modal.querySelector('.modal__dialog');
    const dialog_success = modal.querySelector('.modal__success');
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

    form.addEventListener("submit", async function(e) {
        e.preventDefault(); 
        e.stopPropagation();
        e.stopImmediatePropagation();
        const formData = new FormData(this);
      
        let response = await fetch(window.DJANGO_URLS.form_url, {
          method: "POST",
          body: formData,
          headers: {
            "X-Requested-With": "XMLHttpRequest"
          },
          credentials: 'same-origin'
        });

        dialog.classList.add('hide');
        dialog_success.classList.remove('hide');
        let isJSON = response.headers.get('content-type')?.includes('application/json');
        let data = isJSON ? await response.json() : await response.text();
        //let data = await response.json();
        console.log(data);
        return false;
    });

    function refreshState(){
        form.reset();
        dialog.classList.remove('hide');
        dialog_success.classList.add('hide');
    }
    
    openers.forEach(el=>{
    el.addEventListener('click', function(e){ e.preventDefault(); refreshState(); openModal(); });
    });
    overlay?.addEventListener('click', closeModal);
    closeBtns.forEach(b=> b.addEventListener('click', function(e){ e.preventDefault(); closeModal(); }));
    document.addEventListener('keydown', function(e){
    if(e.key === 'Escape' && modal.classList.contains('is-open')) closeModal();
    });
    });
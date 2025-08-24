document.addEventListener('DOMContentLoaded', function(){
    const modal = document.getElementById('callModal');
    if(!modal) return;
    
    const dialog = modal.querySelector('.modal__dialog');
    const dialog_success = modal.querySelector('.modal__success');
    const form = modal.querySelector('#callForm');
    const openers = document.querySelectorAll('[data-call-modal-open]');
    const overlay = modal.querySelector('.modal__overlay');
    const closeBtns = modal.querySelectorAll('[data-close]');
    
    modal.querySelectorAll('button:not([type])').forEach(b=> b.type='button');
    
    function openModal(){
    modal.classList.add('is-open');
    document.body.classList.add('modal-open');
    setTimeout(()=> form?.querySelector('input[name="name"]')?.focus(), 30);
    }
    function closeModal(){
    modal.classList.remove('is-open');
    document.body.classList.remove('modal-open');
    }
    
    form.querySelectorAll('input, select, textarea').forEach(el=>{
    el.addEventListener('keydown', function(e){
    if(e.key === 'Enter'){
    e.preventDefault();
    form.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}));
    }
    });
    });
    
    let submitting = false;
    form.addEventListener('submit', async function onSubmit(e){
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    
    if(submitting) return;
    submitting = true;
    
    try{
      const formData = new FormData(form);
      const url = form.getAttribute('action') || (window.DJANGO_URLS && window.DJANGO_URLS.form_url);
      if(!url) throw new Error('Нет URL для отправки формы');
    
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
      });
    
      dialog.classList.add('hide');
      dialog_success.classList.remove('hide');
    
      const isJSON = response.headers.get('content-type')?.includes('application/json');
      const data = isJSON ? await response.json() : await response.text();
      console.log('AJAX response:', data);
    }catch(err){
      console.error(err);
      alert('Ошибка отправки. Попробуйте ещё раз.');
    }finally{
      submitting = false;
    }
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
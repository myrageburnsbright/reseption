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
    
    let submitBtn = form.querySelector('#callSubmitBtn');
    if(!submitBtn){
    let existing = form.querySelector('button[type="submit"], input[type="submit"], .btn-primary');
    if(existing){
    if(existing.tagName.toLowerCase()==='input'){
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'callSubmitBtn';
    btn.className = existing.className || 'btn-primary';
    btn.textContent = existing.value || existing.textContent || 'Send';
    existing.replaceWith(btn);
    submitBtn = btn;
    }else{
    existing.type = 'button';
    if(!existing.id) existing.id = 'callSubmitBtn';
    submitBtn = existing;
    }
    }else{
    submitBtn = document.createElement('button');
    submitBtn.type = 'button';
    submitBtn.id = 'callSubmitBtn';
    submitBtn.className = 'btn-primary';
    submitBtn.textContent = 'Send';
    form.appendChild(submitBtn);
    }
    }
    
    form.setAttribute('novalidate','novalidate');
    form.addEventListener('submit', function(e){
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    return false;
    }, true);
    
    form.addEventListener('keydown', function(e){
    if(e.key === 'Enter'){
    e.preventDefault();
    e.stopPropagation();
    sendForm();
    }
    });
    
    submitBtn.addEventListener('click', function(e){
    e.preventDefault();
    sendForm();
    });
    
    function openModal(){
    modal.classList.add('is-open');
    document.body.classList.add('modal-open');
    setTimeout(()=> form?.querySelector('input[name="name"]')?.focus(), 30);
    }
    function closeModal(){
    modal.classList.remove('is-open');
    document.body.classList.remove('modal-open');
    }
    
    let submitting = false;
    async function sendForm(){
    if(submitting) return;
    submitting = true;
    try{
    const formData = new FormData(form);
    const url = form.getAttribute('action') || (window.DJANGO_URLS && window.DJANGO_URLS.form_url);
    if(!url) throw new Error('Нет URL для отправки формы');
    
      const response = await fetch(url, {
        method: 'POST',
        body: formData, // содержит {% csrf_token %}
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
      });
    
      dialog?.classList.add('hide');
      dialog_success?.classList.remove('hide');
    
      const isJSON = response.headers.get('content-type')?.includes('application/json');
      const data = isJSON ? await response.json() : await response.text();
      console.log('AJAX response:', data);
    }catch(err){
      console.error(err);
      alert('Ошибка отправки. Попробуйте ещё раз.');
    }finally{
      submitting = false;
    }
    }
    
    function refreshState(){
    form.reset();
    dialog?.classList.remove('hide');
    dialog_success?.classList.add('hide');
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
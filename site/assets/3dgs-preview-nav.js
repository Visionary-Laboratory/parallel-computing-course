(() => {
 const root = document.querySelector('meta[name="course-root"]')?.content || './';
 const href = root + 'lectures/3d-gaussian-splatting/';
 function attach() {
   const sidebar = document.querySelector('.course-nav');
   if (sidebar && !sidebar.querySelector('[data-gs-draft]')) {
     const a=document.createElement('a'); a.href=href; a.dataset.gsDraft='';
     a.className='lesson-link'; a.textContent='GS · 3D Gaussian Splatting（本地草稿）';
     a.style.cssText='margin-top:16px;padding:12px;color:#176653;border-top:1px solid #e2e9e4';
     sidebar.append(a);
   }
   const syllabus=document.querySelector('#syllabus');
   if(syllabus && !syllabus.querySelector('[data-gs-draft]')) {
     const a=document.createElement('a'); a.href=href; a.dataset.gsDraft='';
     a.textContent='本地草稿 · 3D Gaussian Splatting：从三维表示到 GPU 并行渲染 →';
     a.style.cssText='display:block;margin-top:24px;padding:20px;border:1px solid #bfd5c5;border-radius:8px;background:#f3f8f5;color:#176653';
     syllabus.append(a);
   }
 }
 new MutationObserver(attach).observe(document.body,{childList:true,subtree:true}); attach();
})();

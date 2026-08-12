document.getElementById('showLogin').addEventListener('click', function(){
  document.getElementById('loginForm').classList.remove('hidden');
  document.getElementById('registerForm').classList.add('hidden');
  this.classList.add('active'); document.getElementById('showRegister').classList.remove('active');
});

document.getElementById('showRegister').addEventListener('click', function(){
  document.getElementById('registerForm').classList.remove('hidden');
  document.getElementById('loginForm').classList.add('hidden');
  this.classList.add('active'); document.getElementById('showLogin').classList.remove('active');
});

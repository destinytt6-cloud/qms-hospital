// QMS 系统全局 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');

    if (token && userStr) {
        const user = JSON.parse(userStr);

        // 显示用户信息
        document.getElementById('loginBtn').style.display = 'none';
        document.getElementById('userMenu').style.display = 'block';
        document.getElementById('userName').textContent = user.full_name || user.username;
        document.getElementById('userRole').textContent = user.department
            ? `${user.role} · ${user.department}`
            : user.role;

        // 管理员菜单
        if (user.role === 'admin') {
            document.getElementById('adminMenu').style.display = 'block';
        }
    } else {
        // 未登录时跳转到登录页，但排除登录页本身
        if (!window.location.pathname.startsWith('/login') && window.location.pathname !== '/') {
            window.location.href = '/login';
        }
    }
});

// 退出登录
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

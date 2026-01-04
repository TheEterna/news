/**
 * AI 新闻搜集系统 - 设计系统 JavaScript 工具库
 * Design System v2.0
 */

// ========== 加载遮罩控制器 ==========
const LoadingOverlay = {
    element: null,
    textElement: null,
    
    init() {
        this.element = document.getElementById('loadingOverlay');
        this.textElement = document.getElementById('loadingText');
    },
    
    show(text = 'Processing') {
        if (!this.element) this.init();
        if (this.element && this.textElement) {
            this.textElement.textContent = text;
            this.element.classList.remove('hidden');
            this.element.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    },
    
    hide() {
        if (!this.element) this.init();
        if (this.element) {
            this.element.classList.add('hidden');
            this.element.style.display = 'none';
            document.body.style.overflow = '';
        }
    },
    
    // 带延迟的隐藏（用于动画过渡）
    hideWithDelay(delay = 300) {
        setTimeout(() => this.hide(), delay);
    }
};

// ========== Spring 动画控制器 ==========
const SpringAnimator = {
    // 动画曲线预设
    presets: {
        gentle: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        smooth: 'cubic-bezier(0.4, 0, 0.2, 1)'
    },
    
    /**
     * 为元素应用动画
     * @param {HTMLElement} element - 目标元素
     * @param {Object} properties - CSS 属性对象
     * @param {number} duration - 动画时长（毫秒）
     * @param {string} easing - 缓动函数名称
     * @returns {Promise} - 动画完成后 resolve
     */
    animate(element, properties, duration = 600, easing = 'spring') {
        return new Promise((resolve) => {
            if (!element) {
                resolve();
                return;
            }
            
            const easingFunc = this.presets[easing] || this.presets.spring;
            element.style.transition = `all ${duration}ms ${easingFunc}`;
            
            // 应用属性
            Object.keys(properties).forEach(prop => {
                element.style[prop] = properties[prop];
            });
            
            // 动画完成后清理
            setTimeout(() => {
                element.style.transition = '';
                resolve();
            }, duration);
        });
    },
    
    /**
     * 弹跳进入动画
     * @param {HTMLElement} element - 目标元素
     * @param {number} delay - 延迟时间（毫秒）
     */
    bounceIn(element, delay = 0) {
        if (!element) return;
        
        element.style.opacity = '0';
        element.style.transform = 'scale(0.9) translateY(20px)';
        
        setTimeout(() => {
            this.animate(element, {
                opacity: '1',
                transform: 'scale(1) translateY(0)'
            }, 500, 'bounce');
        }, delay);
    },
    
    /**
     * 滑入动画
     * @param {HTMLElement} element - 目标元素
     * @param {string} direction - 方向 (up, down, left, right)
     * @param {number} delay - 延迟时间（毫秒）
     */
    slideIn(element, direction = 'up', delay = 0) {
        if (!element) return;
        
        const transforms = {
            up: 'translateY(20px)',
            down: 'translateY(-20px)',
            left: 'translateX(20px)',
            right: 'translateX(-20px)'
        };
        
        element.style.opacity = '0';
        element.style.transform = transforms[direction] || transforms.up;
        
        setTimeout(() => {
            this.animate(element, {
                opacity: '1',
                transform: 'translate(0)'
            }, 500, 'gentle');
        }, delay);
    },
    
    /**
     * 交错动画（用于列表）
     * @param {NodeList|Array} elements - 元素列表
     * @param {string} animationType - 动画类型 (bounceIn, slideIn)
     * @param {number} staggerDelay - 交错延迟（毫秒）
     */
    stagger(elements, animationType = 'bounceIn', staggerDelay = 100) {
        const elementsArray = Array.from(elements);
        
        elementsArray.forEach((element, index) => {
            const delay = index * staggerDelay;
            
            if (animationType === 'bounceIn') {
                this.bounceIn(element, delay);
            } else if (animationType === 'slideIn') {
                this.slideIn(element, 'up', delay);
            }
        });
    }
};

// ========== 响应式断点管理器 ==========
const ResponsiveManager = {
    breakpoints: {
        mobile: '(max-width: 767px)',
        tablet: '(min-width: 768px) and (max-width: 1023px)',
        desktop: '(min-width: 1024px)'
    },
    
    listeners: [],
    
    /**
     * 获取当前断点
     * @returns {string} - 当前断点名称
     */
    getCurrentBreakpoint() {
        if (window.matchMedia(this.breakpoints.mobile).matches) return 'mobile';
        if (window.matchMedia(this.breakpoints.tablet).matches) return 'tablet';
        return 'desktop';
    },
    
    /**
     * 检查是否为移动端
     * @returns {boolean}
     */
    isMobile() {
        return this.getCurrentBreakpoint() === 'mobile';
    },
    
    /**
     * 检查是否为平板
     * @returns {boolean}
     */
    isTablet() {
        return this.getCurrentBreakpoint() === 'tablet';
    },
    
    /**
     * 检查是否为桌面端
     * @returns {boolean}
     */
    isDesktop() {
        return this.getCurrentBreakpoint() === 'desktop';
    },
    
    /**
     * 监听断点变化
     * @param {Function} callback - 回调函数，接收新断点名称
     */
    onBreakpointChange(callback) {
        this.listeners.push(callback);
        
        Object.values(this.breakpoints).forEach(query => {
            const mql = window.matchMedia(query);
            mql.addEventListener('change', () => {
                const newBreakpoint = this.getCurrentBreakpoint();
                this.listeners.forEach(cb => cb(newBreakpoint));
            });
        });
    },
    
    /**
     * 移除监听器
     * @param {Function} callback - 要移除的回调函数
     */
    removeListener(callback) {
        this.listeners = this.listeners.filter(cb => cb !== callback);
    }
};

// ========== 性能管理器 ==========
const PerformanceManager = {
    /**
     * 检测是否为低性能设备
     * @returns {boolean}
     */
    isLowPerformance() {
        // 检查 CPU 核心数
        const lowCores = navigator.hardwareConcurrency < 4;
        // 检查设备像素比（高 DPI 设备渲染压力大）
        const highDPI = window.devicePixelRatio > 2;
        // 检查是否为移动设备
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        return lowCores || (highDPI && isMobile);
    },
    
    /**
     * 获取动画级别
     * @returns {string} - 'full', 'reduced', 'minimal'
     */
    getAnimationLevel() {
        // 用户偏好减少动画
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return 'minimal';
        }
        
        // 低性能设备
        if (this.isLowPerformance()) {
            return 'reduced';
        }
        
        return 'full';
    },
    
    /**
     * 应用动画级别到文档
     */
    applyAnimationLevel() {
        const level = this.getAnimationLevel();
        document.documentElement.setAttribute('data-animation-level', level);
        
        if (level !== 'full') {
            console.log(`动画级别: ${level} (已优化以提升性能)`);
        }
        
        return level;
    },
    
    /**
     * 检测是否支持 backdrop-filter
     * @returns {boolean}
     */
    supportsBackdropFilter() {
        return CSS.supports('backdrop-filter', 'blur(1px)') || 
               CSS.supports('-webkit-backdrop-filter', 'blur(1px)');
    },
    
    /**
     * 应用玻璃拟态降级
     */
    applyGlassFallback() {
        if (!this.supportsBackdropFilter()) {
            document.documentElement.classList.add('no-backdrop-filter');
            console.log('玻璃拟态效果已降级（浏览器不支持 backdrop-filter）');
        }
    }
};

// ========== 主题管理器 ==========
const ThemeManager = {
    currentTheme: 'light',
    
    /**
     * 初始化主题
     */
    init() {
        // 检查本地存储
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            this.setTheme(savedTheme);
            return;
        }
        
        // 检查系统偏好
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.setTheme('dark');
        } else {
            this.setTheme('light');
        }
        
        // 监听系统主题变化
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    },
    
    /**
     * 设置主题
     * @param {string} theme - 'light' 或 'dark'
     */
    setTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    },
    
    /**
     * 切换主题
     */
    toggle() {
        this.setTheme(this.currentTheme === 'light' ? 'dark' : 'light');
    },
    
    /**
     * 获取当前主题
     * @returns {string}
     */
    getTheme() {
        return this.currentTheme;
    }
};

// ========== 工具函数 ==========
const Utils = {
    /**
     * 防抖函数
     * @param {Function} func - 要防抖的函数
     * @param {number} wait - 等待时间（毫秒）
     * @returns {Function}
     */
    debounce(func, wait = 300) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * 节流函数
     * @param {Function} func - 要节流的函数
     * @param {number} limit - 时间限制（毫秒）
     * @returns {Function}
     */
    throttle(func, limit = 300) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    /**
     * 格式化数字（添加千分位）
     * @param {number} num - 数字
     * @returns {string}
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },
    
    /**
     * 格式化日期
     * @param {Date|string} date - 日期
     * @param {string} format - 格式 ('short', 'long', 'relative')
     * @returns {string}
     */
    formatDate(date, format = 'short') {
        const d = new Date(date);
        
        if (format === 'relative') {
            const now = new Date();
            const diff = now - d;
            const minutes = Math.floor(diff / 60000);
            const hours = Math.floor(diff / 3600000);
            const days = Math.floor(diff / 86400000);
            
            if (minutes < 1) return '刚刚';
            if (minutes < 60) return `${minutes} 分钟前`;
            if (hours < 24) return `${hours} 小时前`;
            if (days < 7) return `${days} 天前`;
        }
        
        if (format === 'long') {
            return d.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
        
        return d.toLocaleDateString('zh-CN');
    },
    
    /**
     * 复制文本到剪贴板
     * @param {string} text - 要复制的文本
     * @returns {Promise<boolean>}
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('复制失败:', err);
            return false;
        }
    },
    
    /**
     * 生成唯一 ID
     * @returns {string}
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
};

// ========== Toast 通知 ==========
const Toast = {
    container: null,
    
    init() {
        if (this.container) return;
        
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2';
        document.body.appendChild(this.container);
    },
    
    /**
     * 显示 Toast 通知
     * @param {string} message - 消息内容
     * @param {string} type - 类型 ('success', 'error', 'warning', 'info')
     * @param {number} duration - 显示时长（毫秒）
     */
    show(message, type = 'info', duration = 3000) {
        this.init();
        
        const toast = document.createElement('div');
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };
        
        toast.className = `${colors[type] || colors.info} text-white px-6 py-3 rounded-xl shadow-lg animate-slide-down font-medium`;
        toast.textContent = message;
        
        this.container.appendChild(toast);
        
        // 自动移除
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease-out';
            
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },
    
    success(message, duration) {
        this.show(message, 'success', duration);
    },
    
    error(message, duration) {
        this.show(message, 'error', duration);
    },
    
    warning(message, duration) {
        this.show(message, 'warning', duration);
    },
    
    info(message, duration) {
        this.show(message, 'info', duration);
    }
};

// ========== 页面初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
    // 应用性能优化
    PerformanceManager.applyAnimationLevel();
    PerformanceManager.applyGlassFallback();
    
    // 初始化加载遮罩
    LoadingOverlay.init();
    
    // 初始化主题（当前仅支持浅色主题）
    // ThemeManager.init();
    
    console.log('🎨 Design System v2.0 已加载');
    console.log(`📱 当前断点: ${ResponsiveManager.getCurrentBreakpoint()}`);
    console.log(`⚡ 动画级别: ${PerformanceManager.getAnimationLevel()}`);
});

// 导出到全局（用于非模块化环境）
window.DesignSystem = {
    LoadingOverlay,
    SpringAnimator,
    ResponsiveManager,
    PerformanceManager,
    ThemeManager,
    Utils,
    Toast
};
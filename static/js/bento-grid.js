/**
 * Bento Grid 布局系统
 * 实现类似日式便当盒的不规则网格布局
 */

// ========== Bento Grid 管理器 ==========
class BentoGrid {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
        
        if (!this.container) {
            console.error('BentoGrid: 容器元素未找到');
            return;
        }
        
        // 默认配置
        this.options = {
            columns: {
                mobile: 1,
                tablet: 3,
                desktop: 4
            },
            gap: 16,
            rowHeight: 180,
            animateOnLoad: true,
            staggerDelay: 100,
            ...options
        };
        
        this.cards = [];
        this.currentBreakpoint = this.getCurrentBreakpoint();
        
        this.init();
    }
    
    /**
     * 初始化网格
     */
    init() {
        // 添加网格类
        this.container.classList.add('bento-grid');
        
        // 应用样式
        this.applyGridStyles();
        
        // 收集卡片
        this.collectCards();
        
        // 监听窗口大小变化
        this.setupResizeListener();
        
        // 入场动画
        if (this.options.animateOnLoad) {
            this.animateCardsIn();
        }
        
        console.log(`BentoGrid 初始化完成 | 卡片数: ${this.cards.length}`);
    }
    
    /**
     * 获取当前断点
     */
    getCurrentBreakpoint() {
        if (window.matchMedia('(max-width: 767px)').matches) return 'mobile';
        if (window.matchMedia('(max-width: 1023px)').matches) return 'tablet';
        return 'desktop';
    }
    
    /**
     * 应用网格样式
     */
    applyGridStyles() {
        const breakpoint = this.getCurrentBreakpoint();
        const columns = this.options.columns[breakpoint];
        
        this.container.style.display = 'grid';
        this.container.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
        this.container.style.gap = `${this.options.gap}px`;
        this.container.style.gridAutoRows = `${this.options.rowHeight}px`;
    }
    
    /**
     * 收集所有卡片元素
     */
    collectCards() {
        this.cards = Array.from(this.container.querySelectorAll('.bento-card, [data-bento-card]'));
    }
    
    /**
     * 设置窗口大小变化监听
     */
    setupResizeListener() {
        let resizeTimeout;
        
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                const newBreakpoint = this.getCurrentBreakpoint();
                
                if (newBreakpoint !== this.currentBreakpoint) {
                    this.currentBreakpoint = newBreakpoint;
                    this.applyGridStyles();
                    this.onBreakpointChange(newBreakpoint);
                }
            }, 150);
        });
    }
    
    /**
     * 断点变化回调
     */
    onBreakpointChange(breakpoint) {
        console.log(`BentoGrid 断点变化: ${breakpoint}`);
        
        // 触发自定义事件
        this.container.dispatchEvent(new CustomEvent('bento:breakpointChange', {
            detail: { breakpoint }
        }));
    }
    
    /**
     * 卡片入场动画
     */
    animateCardsIn() {
        this.cards.forEach((card, index) => {
            // 初始状态
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px) scale(0.95)';
            
            // 延迟动画
            setTimeout(() => {
                card.style.transition = 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0) scale(1)';
                
                // 动画完成后清理
                setTimeout(() => {
                    card.style.transition = '';
                }, 500);
            }, index * this.options.staggerDelay);
        });
    }
    
    /**
     * 添加新卡片
     */
    addCard(cardElement, position = 'end') {
        if (position === 'start') {
            this.container.prepend(cardElement);
        } else {
            this.container.appendChild(cardElement);
        }
        
        this.collectCards();
        
        // 入场动画
        cardElement.style.opacity = '0';
        cardElement.style.transform = 'translateY(20px) scale(0.95)';
        
        requestAnimationFrame(() => {
            cardElement.style.transition = 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
            cardElement.style.opacity = '1';
            cardElement.style.transform = 'translateY(0) scale(1)';
        });
    }
    
    /**
     * 移除卡片
     */
    removeCard(cardElement) {
        return new Promise((resolve) => {
            cardElement.style.transition = 'all 0.3s ease-out';
            cardElement.style.opacity = '0';
            cardElement.style.transform = 'scale(0.9)';
            
            setTimeout(() => {
                cardElement.remove();
                this.collectCards();
                resolve();
            }, 300);
        });
    }
    
    /**
     * 刷新网格
     */
    refresh() {
        this.collectCards();
        this.applyGridStyles();
    }
    
    /**
     * 销毁网格
     */
    destroy() {
        this.container.classList.remove('bento-grid');
        this.container.style.display = '';
        this.container.style.gridTemplateColumns = '';
        this.container.style.gap = '';
        this.container.style.gridAutoRows = '';
        
        this.cards = [];
    }
}

// ========== Bento Card 组件 ==========
class BentoCard {
    constructor(config) {
        this.config = {
            id: config.id || `bento-card-${Date.now()}`,
            type: config.type || 'default',
            title: config.title || '',
            subtitle: config.subtitle || '',
            content: config.content || '',
            icon: config.icon || null,
            image: config.image || null,
            gradient: config.gradient || null,
            colSpan: config.colSpan || 1,
            rowSpan: config.rowSpan || 1,
            onClick: config.onClick || null,
            className: config.className || '',
            ...config
        };
        
        this.element = null;
        this.render();
    }
    
    /**
     * 渲染卡片
     */
    render() {
        this.element = document.createElement('div');
        this.element.id = this.config.id;
        this.element.className = this.buildClassName();
        this.element.innerHTML = this.buildContent();
        
        // 应用网格跨度
        this.applyGridSpan();
        
        // 绑定事件
        this.bindEvents();
        
        return this.element;
    }
    
    /**
     * 构建类名
     */
    buildClassName() {
        const classes = [
            'bento-card',
            'glass-card',
            'rounded-3xl',
            'p-6',
            'md:p-8',
            'gentle-transition',
            'hover:scale-[1.02]',
            'hover:-translate-y-1',
            'cursor-pointer',
            'group',
            'relative',
            'overflow-hidden'
        ];
        
        if (this.config.className) {
            classes.push(this.config.className);
        }
        
        return classes.join(' ');
    }
    
    /**
     * 应用网格跨度
     */
    applyGridSpan() {
        const { colSpan, rowSpan } = this.config;
        
        // 响应式跨度
        if (colSpan > 1) {
            this.element.style.gridColumn = `span ${colSpan}`;
        }
        
        if (rowSpan > 1) {
            this.element.style.gridRow = `span ${rowSpan}`;
        }
    }
    
    /**
     * 构建内容
     */
    buildContent() {
        const { type } = this.config;
        
        switch (type) {
            case 'search':
                return this.buildSearchContent();
            case 'stats':
                return this.buildStatsContent();
            case 'action':
                return this.buildActionContent();
            case 'preview':
                return this.buildPreviewContent();
            default:
                return this.buildDefaultContent();
        }
    }
    
    /**
     * 默认内容
     */
    buildDefaultContent() {
        const { title, subtitle, content, icon } = this.config;
        
        return `
            <div class="flex flex-col h-full justify-between">
                ${icon ? `
                    <div class="p-3 rounded-2xl bg-gray-100 w-fit text-gray-700">
                        ${icon}
                    </div>
                ` : ''}
                <div class="mt-auto">
                    ${title ? `<h3 class="text-xl font-bold text-gray-900 mb-1">${title}</h3>` : ''}
                    ${subtitle ? `<p class="text-sm text-gray-500">${subtitle}</p>` : ''}
                    ${content ? `<p class="text-gray-600 mt-2">${content}</p>` : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * 搜索卡片内容
     */
    buildSearchContent() {
        const { title, subtitle } = this.config;
        
        return `
            <div class="flex flex-col h-full">
                <div class="flex justify-between items-start mb-4">
                    <div class="p-3 rounded-2xl gradient-blue-purple text-white">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.35-4.35"></path>
                        </svg>
                    </div>
                    <span class="tag tag-success">Active</span>
                </div>
                <div class="flex-1">
                    ${title ? `<h2 class="text-2xl font-bold text-gray-900 mb-2">${title}</h2>` : ''}
                    ${subtitle ? `<p class="text-gray-600 text-sm">${subtitle}</p>` : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * 统计卡片内容
     */
    buildStatsContent() {
        const { title, value, label, trend } = this.config;
        
        return `
            <div class="flex flex-col h-full justify-between">
                <div class="flex justify-between items-center">
                    <div class="p-2 rounded-lg bg-gray-100 text-gray-700">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"></path>
                        </svg>
                    </div>
                    ${trend ? `<span class="text-xs text-green-600 font-mono">${trend}</span>` : ''}
                </div>
                <div>
                    ${value ? `<p class="text-4xl font-bold text-gray-900 mb-1">${value}</p>` : ''}
                    ${label ? `<p class="text-sm text-gray-500 uppercase tracking-wider">${label}</p>` : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * 操作卡片内容
     */
    buildActionContent() {
        const { title, subtitle, icon } = this.config;
        
        return `
            <div class="flex flex-col items-center justify-center h-full text-center gap-4">
                ${icon ? `
                    <div class="p-4 rounded-full gradient-green-blue text-white scale-125 group-hover:scale-150 spring-transition">
                        ${icon}
                    </div>
                ` : ''}
                <div>
                    ${title ? `<p class="font-bold text-sm text-gray-900">${title}</p>` : ''}
                    ${subtitle ? `<p class="text-xs text-gray-500 mt-1">${subtitle}</p>` : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * 预览卡片内容
     */
    buildPreviewContent() {
        const { title, subtitle, stats } = this.config;
        
        return `
            <div class="flex flex-col h-full justify-between">
                <div>
                    <div class="inline-block px-3 py-1 mb-4 rounded-full bg-purple-100 text-purple-700 text-xs font-bold uppercase tracking-wider">
                        Preview
                    </div>
                    ${title ? `<h3 class="text-2xl font-bold text-gray-900 mb-2">${title}</h3>` : ''}
                    ${subtitle ? `<p class="text-gray-600">${subtitle}</p>` : ''}
                </div>
                ${stats ? `
                    <div class="grid grid-cols-3 gap-4 mt-4">
                        ${stats.map(stat => `
                            <div class="text-center p-3 rounded-xl bg-white/50">
                                <p class="text-xl font-bold text-gray-900">${stat.value}</p>
                                <p class="text-xs text-gray-500 mt-1">${stat.label}</p>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        if (this.config.onClick) {
            this.element.addEventListener('click', (e) => {
                this.config.onClick(e, this);
            });
        }
        
        // 悬停效果增强
        this.element.addEventListener('mouseenter', () => {
            this.element.style.transform = 'translateY(-4px) scale(1.02)';
        });
        
        this.element.addEventListener('mouseleave', () => {
            this.element.style.transform = '';
        });
    }
    
    /**
     * 更新卡片内容
     */
    update(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.element.innerHTML = this.buildContent();
    }
    
    /**
     * 获取 DOM 元素
     */
    getElement() {
        return this.element;
    }
    
    /**
     * 销毁卡片
     */
    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}

// ========== 工厂函数 ==========

/**
 * 创建 Bento Grid
 */
function createBentoGrid(container, options) {
    return new BentoGrid(container, options);
}

/**
 * 创建 Bento Card
 */
function createBentoCard(config) {
    return new BentoCard(config);
}

// 导出到全局
window.BentoGrid = BentoGrid;
window.BentoCard = BentoCard;
window.createBentoGrid = createBentoGrid;
window.createBentoCard = createBentoCard;
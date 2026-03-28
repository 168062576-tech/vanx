/**
 * i18n 国际化引擎
 * 支持中英文切换
 */

class I18n {
    constructor() {
        this.currentLang = localStorage.getItem('vanx-lang') || 'zh';
        this.translations = {};
        this.loaded = false;
    }

    // 加载翻译文件
    async load(lang) {
        try {
            const response = await fetch(`/js/lang-${lang}.json`);
            if (!response.ok) throw new Error(`Failed to load ${lang}`);
            this.translations[lang] = await response.json();
            return true;
        } catch (error) {
            console.error(`i18n: Failed to load ${lang}:`, error);
            return false;
        }
    }

    // 初始化（加载两种语言）
    async init() {
        await Promise.all([
            this.load('zh'),
            this.load('en')
        ]);
        this.loaded = true;
        this.applyLanguage(this.currentLang);
    }

    // 翻译函数
    t(key, defaultText = '') {
        const keys = key.split('.');
        let value = this.translations[this.currentLang];
        
        for (const k of keys) {
            value = value?.[k];
        }
        
        return value || defaultText;
    }

    // 应用语言
    applyLanguage(lang) {
        this.currentLang = lang;
        localStorage.setItem('vanx-lang', lang);
        
        // 更新所有带 data-i18n 属性的元素
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const defaultText = el.getAttribute('data-i18n-default') || el.textContent;
            el.textContent = this.t(key, defaultText);
        });
        
        // 更新 placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = this.t(key, '');
        });
        
        // 更新 title
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            el.title = this.t(key, '');
        });

        // 触发语言切换事件
        window.dispatchEvent(new CustomEvent('langChanged', { detail: { lang } }));
    }

    // 切换语言
    toggle() {
        const newLang = this.currentLang === 'zh' ? 'en' : 'zh';
        this.applyLanguage(newLang);
        return newLang;
    }

    // 获取当前语言
    getLang() {
        return this.currentLang;
    }

    // 获取语言名称
    getLangName() {
        return this.translations[this.currentLang]?.meta?.name || this.currentLang;
    }
}

// 创建全局实例
window.i18n = new I18n();

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async () => {
    await window.i18n.init();
    console.log('i18n: Initialized with', window.i18n.getLang());
});

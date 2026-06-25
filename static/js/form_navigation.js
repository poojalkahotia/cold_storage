(function () {
    if (window.FormNavigationModuleLoaded) {
        return;
    }
    window.FormNavigationModuleLoaded = true;

    var SELECT2_SEARCH_SELECTOR = '.select2-search__field';
    var SELECT2_CONTAINER_SELECTOR = '.select2-container';
    var SUPPORTED_INPUT_TYPES = [
        'text',
        'email',
        'tel',
        'number',
        'date',
        'time',
        'search',
        'url',
        'password',
        'datetime-local'
    ];

    function isVisible(element) {
        if (!element || !element.offsetParent) {
            return element && element.matches('select.select2-hidden-accessible');
        }
        var style = window.getComputedStyle(element);
        return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
    }

    function isPrimarySubmitButton(button) {
        if (!button || (button.tagName !== 'BUTTON' && button.tagName !== 'INPUT')) {
            return false;
        }
        if (button.disabled || !isVisible(button)) {
            return false;
        }
        if (button.type !== 'submit' && button.type !== 'button') {
            return false;
        }
        if (button.type === 'submit') {
            return true;
        }
        return false;
    }

    function isSaveButton(button) {
        if (!isPrimarySubmitButton(button)) {
            return false;
        }
        if (button.tagName === 'INPUT') {
            return true;
        }
        var text = (button.textContent || button.value || '').trim().toLowerCase();
        return text === 'save' || text === 'submit' || text === 'update' || button.classList.contains('btn-primary');
    }

    function isHiddenByType(element) {
        return element.tagName === 'INPUT' && element.type === 'hidden';
    }

    function isReadonly(element) {
        return element.hasAttribute('readonly');
    }

    function isSelectableByEnter(element) {
        return element.matches(SELECT2_SEARCH_SELECTOR) || element.closest(SELECT2_CONTAINER_SELECTOR);
    }

    function isSupportedField(element) {
        if (!element || element.disabled || !isVisible(element)) {
            return false;
        }
        if (element.tagName === 'TEXTAREA') {
            return true;
        }
        if (element.tagName === 'SELECT') {
            return true;
        }
        if (element.tagName !== 'INPUT') {
            return false;
        }
        if (isHiddenByType(element)) {
            return false;
        }
        if (isReadonly(element)) {
            return false;
        }
        if (element.type === 'checkbox' || element.type === 'radio') {
            return true;
        }
        return SUPPORTED_INPUT_TYPES.indexOf(element.type) !== -1;
    }

    function findClosestForm(element) {
        return element && (element.form || element.closest('form'));
    }

    function isSubmitControl(element) {
        return element && ((element.tagName === 'BUTTON' && element.type === 'submit') || (element.tagName === 'INPUT' && element.type === 'submit'));
    }

    function isIgnoredButton(element) {
        if (!element) {
            return false;
        }
        if (element.tagName === 'BUTTON' || element.tagName === 'INPUT') {
            if (element.type === 'reset' || element.type === 'button' || element.type === 'image') {
                return true;
            }
            var label = (element.textContent || element.value || '').trim().toLowerCase();
            return /cancel|back|exit|delete|reset/.test(label);
        }
        return false;
    }

    function getFocusableFields(form) {
        if (!form) {
            return [];
        }
        var candidateSelector = 'input:not([disabled]), textarea:not([disabled]), select:not([disabled])';
        var candidates = Array.prototype.slice.call(form.querySelectorAll(candidateSelector));
        var focusable = candidates.filter(function (candidate) {
            if (!isSupportedField(candidate)) {
                return false;
            }
            if (candidate.tagName === 'SELECT' && candidate.classList.contains('select2-hidden-accessible')) {
                return true;
            }
            if (candidate.tagName === 'SELECT' && !candidate.classList.contains('select2-hidden-accessible')) {
                return true;
            }
            if (candidate.tagName === 'INPUT' && candidate.type === 'button') {
                return false;
            }
            if (candidate.tagName === 'INPUT' && candidate.type === 'submit') {
                return false;
            }
            return true;
        });
        return focusable;
    }

    function findSelect2Original(element) {
        if (!element) {
            return null;
        }
        if (element.matches('select.select2-hidden-accessible')) {
            return element;
        }
        var container = element.closest(SELECT2_CONTAINER_SELECTOR);
        if (!container) {
            return null;
        }
        var previous = container.previousElementSibling;
        if (previous && previous.matches('select.select2-hidden-accessible')) {
            return previous;
        }
        var next = container.nextElementSibling;
        if (next && next.matches('select.select2-hidden-accessible')) {
            return next;
        }
        var form = findClosestForm(element);
        if (!form) {
            return null;
        }
        var selects = form.querySelectorAll('select.select2-hidden-accessible');
        for (var i = 0; i < selects.length; i += 1) {
            if (selects[i].nextElementSibling === container || selects[i].previousElementSibling === container) {
                return selects[i];
            }
        }
        return null;
    }

    function findNextField(current) {
        if (!current) {
            return null;
        }
        var form = findClosestForm(current);
        if (!form) {
            return null;
        }
        var fields = getFocusableFields(form);
        var currentField = current;
        if (!fields.includes(currentField) && isSelectableByEnter(currentField)) {
            var original = findSelect2Original(currentField);
            if (original) {
                currentField = original;
            }
        }
        var index = fields.indexOf(currentField);
        if (index === -1) {
            return null;
        }
        for (var nextIndex = index + 1; nextIndex < fields.length; nextIndex += 1) {
            var candidate = fields[nextIndex];
            if (candidate.tagName === 'BUTTON' || candidate.tagName === 'INPUT') {
                if (isIgnoredButton(candidate)) {
                    continue;
                }
                if (candidate.type === 'submit') {
                    continue;
                }
            }
            return candidate;
        }
        return null;
    }

    function focusElement(element) {
        if (!element) {
            return;
        }
        try {
            element.focus();
        } catch (ignore) {
        }
    }

    function focusPrimarySave(form) {
        if (!form) {
            return;
        }
        var candidates = Array.prototype.slice.call(form.querySelectorAll('button[type="submit"], input[type="submit"]'));
        candidates = candidates.filter(function (el) {
            return isVisible(el) && !el.disabled && !isIgnoredButton(el);
        });
        if (candidates.length === 0) {
            return;
        }
        var primary = candidates.find(function (button) {
            return isSaveButton(button);
        });
        focusElement(primary || candidates[0]);
    }

    function handleCheckboxEnter(element, event) {
        if (!element || element.type !== 'checkbox') {
            return false;
        }
        if (!element.__enterTogglePending) {
            element.checked = !element.checked;
            element.dispatchEvent(new Event('change', { bubbles: true }));
            element.__enterTogglePending = true;
            event.preventDefault();
            return true;
        }
        element.__enterTogglePending = false;
        return false;
    }

    function resetCheckboxPending(event) {
        var target = event.target;
        if (target && target.type === 'checkbox') {
            target.__enterTogglePending = false;
        }
    }

    function isSelect2SearchField(element) {
        return element.matches(SELECT2_SEARCH_SELECTOR) || !!element.closest(SELECT2_CONTAINER_SELECTOR);
    }

    function handleEnterKey(event) {
        if (event.key !== 'Enter') {
            return;
        }
        var target = event.target;
        if (!target) {
            return;
        }
        if (target.tagName === 'BUTTON' || target.tagName === 'INPUT' && target.type === 'submit') {
            return;
        }
        if (target.tagName === 'TEXTAREA') {
            if (event.ctrlKey || event.metaKey) {
                return;
            }
            event.preventDefault();
            var next = findNextField(target);
            if (next) {
                focusElement(next);
            } else {
                focusPrimarySave(findClosestForm(target));
            }
            return;
        }
        if (target.type === 'checkbox') {
            if (handleCheckboxEnter(target, event)) {
                return;
            }
            event.preventDefault();
            var next = findNextField(target);
            if (next) {
                focusElement(next);
            } else {
                focusPrimarySave(findClosestForm(target));
            }
            return;
        }
        if (isSelect2SearchField(target)) {
            return;
        }
        if (target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.tagName === 'TEXTAREA') {
            if (target.tagName === 'INPUT' && target.type === 'radio') {
                event.preventDefault();
                var nextRadio = findNextField(target);
                if (nextRadio) {
                    focusElement(nextRadio);
                } else {
                    focusPrimarySave(findClosestForm(target));
                }
                return;
            }
            event.preventDefault();
            var next = findNextField(target);
            if (next) {
                focusElement(next);
            } else {
                focusPrimarySave(findClosestForm(target));
            }
        }
    }

    function attachSelect2Support() {
        if (!window.jQuery || !window.jQuery.fn || !window.jQuery.fn.select2) {
            return;
        }
        var $ = window.jQuery;
        $(document).on('select2:select', 'select.select2-hidden-accessible', function () {
            var original = this;
            var next = findNextField(original);
            if (next) {
                setTimeout(function () {
                    focusElement(next);
                }, 0);
            } else {
                focusPrimarySave(findClosestForm(original));
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.addEventListener('keydown', handleEnterKey, true);
        document.addEventListener('blur', resetCheckboxPending, true);
        attachSelect2Support();
    });
})();

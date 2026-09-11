/**
 * tour-init — renders a floating "Start tour" launcher on any page that has at
 * least one active tour, and (optionally) auto-opens a tour the first time a
 * visitor lands on a matching page.
 *
 * The list of tours for the current page is embedded server-side in
 * `data-module-config` (`{collapse_steps, launcher_position, tours: [...]}`),
 * so this module makes no XHR. Each tour builds its own Shepherd instance
 * lazily, the first time it is started.
 */
this.ckan.module('tour-init', function (jQuery) {
    return {
        options: {
            config: {
                launcher_position: "bottom-right",
                tours: []
            }
        },

        initialize: function () {
            $.proxyAll(this, /_/);

            this.tours = this.options.config.tours || [];
            this.instances = {};
            this.isMobile = this._isMobile();
            this.previewTour = this._extractPreviewTour();

            if (!this.tours.length && !this.previewTour) {
                return;
            }

            if (this.tours.length) {
                this._renderLauncher();
            }

            if (this.previewTour) {
                this._getInstance(this.previewTour).start();
            } else {
                this._maybeAutoStart();
            }
        },

        /**
         * A tour flagged `preview` is an unsaved tour served only to the
         * admin who hit "Preview" — keep it out of the launcher and play it
         * straight away, ignoring the "seen" flag and the mobile guard
        */
        _extractPreviewTour: function () {
            for (var i = 0; i < this.tours.length; i++) {
                if (this.tours[i].preview) {
                    return this.tours.splice(i, 1)[0];
                }
            }

            return null;
        },

        _isMobile: function () {
            // Auto-start is suppressed on small/touch screens where Shepherd's
            // popup positioning and body-scroll-lock behave poorly.
            if (!window.matchMedia) {
                return false;
            }

            return window.matchMedia("(max-width: 768px), (pointer: coarse)").matches;
        },

        _seenKeyBase: function (tour) {
            return "tour-seen-" + tour.id;
        },

        _seenKey: function (tour) {
            // Version the flag by `modified_at` so editing a tour (or any of
            // its steps — the model bumps `modified_at` for both) re-shows it to
            // people who already dismissed the previous version.
            return this._seenKeyBase(tour) + "-" + (tour.modified_at || "0");
        },

        _renderLauncher: function () {
            var self = this;

            var position = this.options.config.launcher_position === "bottom-left"
                ? "tour-launcher--bottom-left"
                : "tour-launcher--bottom-right";

            this.launcher = $("<button />", {
                type: "button",
                "class": "tour-launcher " + position,
                "aria-label": this._("Start tour"),
                html: '<i class="fa fa-map-signs" aria-hidden="true"></i>'
            });

            if (this.tours.length === 1) {
                this.launcher.attr("title", this.tours[0].title || this._("Start tour"));
                this.launcher.on("click", function () {
                    self._startTour(self.tours[0]);
                });
            } else {
                this.launcher.attr("aria-haspopup", "true");
                this.launcher.attr("aria-expanded", "false");
                this.menu = this._renderMenu();
                this.menuItems = this.menu.find(".tour-launcher-menu__item");
                this.launcher.on("click", this._toggleMenu);
                this.launcher.on("keydown", this._onLauncherKeydown);
                this.menu.on("keydown", this._onMenuKeydown);
                $(document).on("click", this._closeMenuOnOutsideClick);
            }

            $("body").append(this.launcher);

            if (this.menu) {
                $("body").append(this.menu);
            }
        },

        _renderMenu: function () {
            var self = this;
            var position = this.options.config.launcher_position === "bottom-left"
                ? "tour-launcher-menu--bottom-left"
                : "tour-launcher-menu--bottom-right";

            var menu = $("<div />", { "class": "tour-launcher-menu " + position });

            $("<div />", { "class": "tour-launcher-menu__header", text: this._("Start a tour") })
                .appendTo(menu);

            var list = $("<ul />", { "class": "tour-launcher-menu__list", role: "menu" }).appendTo(menu);

            this.tours.forEach(function (tour) {
                var item = $("<li />", { role: "none" });
                var link = $("<button />", {
                    type: "button",
                    role: "menuitem",
                    "class": "tour-launcher-menu__item",
                });

                $("<span />", { "class": "tour-launcher-menu__item-badge" })
                    .append('<i class="fa fa-route" aria-hidden="true"></i>')
                    .appendTo(link);

                $("<span />", {
                    "class": "tour-launcher-menu__item-label",
                    text: tour.title || self._("Untitled tour"),
                }).appendTo(link);

                link.on("click", function () {
                    self._hideMenu();
                    self.launcher.trigger("focus");
                    self._startTour(tour);
                });

                item.append(link);
                list.append(item);
            });

            return menu;
        },

        _toggleMenu: function () {
            if (this.menu.hasClass("tour-launcher-menu--open")) {
                this._hideMenu();
            } else {
                this._showMenu();
            }
        },

        _showMenu: function () {
            this.menu.addClass("tour-launcher-menu--open");
            this.launcher.addClass("tour-launcher--active");
            this.launcher.attr("aria-expanded", "true");
        },

        _hideMenu: function () {
            if (this.menu) {
                this.menu.removeClass("tour-launcher-menu--open");
                this.launcher.removeClass("tour-launcher--active");
                this.launcher.attr("aria-expanded", "false");
            }
        },

        _onLauncherKeydown: function (e) {
            if (e.key !== "ArrowDown" && e.key !== "ArrowUp") {
                return;
            }

            e.preventDefault();
            this._showMenu();
            this._focusMenuItem(e.key === "ArrowDown" ? 0 : this.menuItems.length - 1);
        },

        _onMenuKeydown: function (e) {
            var current = this.menuItems.index(document.activeElement);

            switch (e.key) {
                case "ArrowDown":
                    e.preventDefault();
                    this._focusMenuItem((current + 1) % this.menuItems.length);
                    break;
                case "ArrowUp":
                    e.preventDefault();
                    this._focusMenuItem((current - 1 + this.menuItems.length) % this.menuItems.length);
                    break;
                case "Home":
                    e.preventDefault();
                    this._focusMenuItem(0);
                    break;
                case "End":
                    e.preventDefault();
                    this._focusMenuItem(this.menuItems.length - 1);
                    break;
                case "Escape":
                    e.preventDefault();
                    this._hideMenu();
                    this.launcher.trigger("focus");
                    break;
                case "Tab":
                    // a menu button's popup isn't in the normal tab order --
                    // Tab out of it closes the menu rather than wandering in
                    this._hideMenu();
                    break;
            }
        },

        _focusMenuItem: function (index) {
            this.menuItems.eq(index).trigger("focus");
        },

        _closeMenuOnOutsideClick: function (e) {
            if (!this.menu?.hasClass("tour-launcher-menu--open")) {
                return;
            }

            const $target = $(e.target);

            if (
                this.launcher.is($target) ||
                this.launcher.has($target).length ||
                this.menu.has($target).length
            ) {
                return;
            }

            this._hideMenu();
        },

        _maybeAutoStart: function () {
            if (this.isMobile) {
                return;
            }

            for (var i = 0; i < this.tours.length; i++) {
                var tour = this.tours[i];

                if (!tour.auto_start) {
                    continue;
                }

                if (this._getSeen(tour)) {
                    continue;
                }

                this._setSeen(tour);
                this._startTour(tour);
                return;
            }
        },

        _getSeen: function (tour) {
            try {
                return window.localStorage.getItem(this._seenKey(tour));
            } catch (e) {
                return null;
            }
        },

        _setSeen: function (tour) {
            try {
                this._pruneSeen(tour);
                window.localStorage.setItem(this._seenKey(tour), "1");
            } catch (e) {
                // private mode / storage disabled — auto-start will just repeat
            }
        },

        _pruneSeen: function (tour) {
            // Drop "seen" flags for older versions of this tour (and the legacy
            // unversioned key) so entries don't accumulate over its lifetime.
            var base = this._seenKeyBase(tour);
            var current = this._seenKey(tour);

            for (var i = window.localStorage.length - 1; i >= 0; i--) {
                var key = window.localStorage.key(i);

                if (!key || key === current) {
                    continue;
                }

                if (key === base || key.indexOf(base + "-") === 0) {
                    window.localStorage.removeItem(key);
                }
            }
        },

        _startTour: function (tour) {
            this._setSeen(tour);
            this._getInstance(tour).start();
        },

        _getInstance: function (tour) {
            if (!this.instances[tour.id]) {
                this.instances[tour.id] = this._buildTour(tour);
            }

            return this.instances[tour.id];
        },

        _buildTour: function (tour) {
            var instance = new Shepherd.Tour({
                useModalOverlay: true,
                defaultStepOptions: {
                    floatingUIOptions: { middleware: [FloatingUICore.offset(20)] },
                    cancelIcon: {
                        enabled: true,
                        label: this._("Skip tour")
                    },
                    modalOverlayOpeningPadding: 5,
                    modalOverlayOpeningRadius: 5,
                    classes: 'tour-step',
                    scrollTo: { behavior: 'smooth', block: 'center' },
                    when: {
                        // method refs, not `_`-prefixed, so `$.proxyAll` leaves
                        // them unbound and Shepherd can call them with the step
                        // as `this`
                        show: this.onStepShow,
                        destroy: this.onTourDestroy
                    }
                }
            });

            instance.addSteps(this._prepareSteps(tour.steps || []));

            return instance;
        },

        onStepShow: function () {
            // `this` is the Shepherd step
            bodyScrollLock.disableBodyScroll(".tour-step");

            var currentStep = this;
            var tour = this.tour;
            var currentStepIdx = tour.steps.indexOf(currentStep);
            var stepEl = currentStep.el;

            if (!stepEl) {
                return;
            }

            // a step can be re-shown (back/forward), so drop any stale bullets
            // this step's popup already carries before rebuilding them
            stepEl.querySelectorAll(".shepherd-stats").forEach(function (el) {
                el.remove();
            });

            var progressListEl = document.createElement('ul');
            progressListEl.className = "list-unstyled shepherd-stats";
            progressListEl.setAttribute("aria-label", ckan.i18n._("Tour progress"));

            for (var i = 0; i < tour.steps.length; i++) {
                var itemEl = document.createElement('li');

                var bulletElement = document.createElement('button');
                bulletElement.type = "button";
                bulletElement.className = "shepherd-stats__bullet";
                bulletElement.dataset.stepId = tour.steps[i].id;
                bulletElement.setAttribute(
                    "aria-label",
                    ckan.i18n._("Go to step %(num)s", { num: i + 1 })
                );

                if (i === currentStepIdx) {
                    bulletElement.classList.add("active");
                    bulletElement.setAttribute("aria-current", "step");
                }

                bulletElement.addEventListener("click", function (e) {
                    tour.show(e.currentTarget.dataset.stepId);
                });

                itemEl.appendChild(bulletElement);
                progressListEl.appendChild(itemEl);
            }

            var footer = stepEl.querySelector(".shepherd-footer");
            if (footer) {
                footer.parentNode.insertBefore(progressListEl, footer);
            }
        },

        onTourDestroy: function () {
            bodyScrollLock.clearAllBodyScrollLocks();
        },

        /**
         * Return `selector` only if it is a string a browser can use as a CSS
         * selector; otherwise null. Guards against step `element` values that
         * jQuery would parse as HTML (`<...>`) or that are invalid syntax
         * (which would otherwise throw and abort the tour).
         */
        _safeSelector: function (selector) {
            if (typeof selector !== "string" || selector.indexOf("<") !== -1) {
                return null;
            }

            try {
                document.querySelector(selector);
            } catch (e) {
                return null;
            }

            return selector;
        },

        _prepareSteps: function (steps) {
            var self = this;

            var backText = '<i class="fa fa-arrow-left shepherd-button__icon" aria-hidden="true"></i><span>' + self._("Back") + '</span>';
            var nextText = '<span>' + self._("Next") + '</span><i class="fa fa-arrow-right shepherd-button__icon" aria-hidden="true"></i>';

            steps.forEach(function (step, idx) {
                var isLast = steps.length - 1 === idx;
                var isFirst = idx === 0;
                var lastButtonText = isLast ? self._("Done") : nextText;
                var firstButtonClasses = isFirst ? 'shepherd-back disabled' : 'shepherd-back';

                // `step.intro` is already sanitised HTML, rendered server-side
                if (step.image_url) {
                    var imageData = $("<img />", { src: step.image_url })[0].outerHTML;
                    step.text = (step.intro || "") + "<br>" + imageData;
                } else {
                    step.text = step.intro || "";
                }

                step.buttons = [
                    {
                        action: function () { return this.back(); },
                        classes: firstButtonClasses,
                        text: backText
                    },
                    {
                        action: function () { return this.next(); },
                        classes: 'shepherd-next',
                        text: lastButtonText
                    }
                ];

                var stepSelector = self._safeSelector(step.element);
                if (stepSelector) {
                    step.attachTo = { element: stepSelector, on: step.position };
                }
                // an unsafe/invalid selector leaves the step unattached, so
                // Shepherd renders it as a centered modal instead of throwing
            });

            return steps;
        }
    }
});

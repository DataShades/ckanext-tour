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

            if (!this.tours.length) {
                return;
            }

            this._renderLauncher();
            this._maybeAutoStart();
        },

        _isMobile: function () {
            // Auto-start is suppressed on small/touch screens where Shepherd's
            // popup positioning and body-scroll-lock behave poorly.
            if (!window.matchMedia) {
                return false;
            }

            return window.matchMedia("(max-width: 768px), (pointer: coarse)").matches;
        },

        _seenKey: function (tourId) {
            return "tour-seen-" + tourId;
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
                this.launcher.on("click", this._toggleMenu);
                $(document).on("click", this._closeMenuOnOutsideClick);
            }

            $("body").append(this.launcher);

            if (this.menu) {
                $("body").append(this.menu);
            }
        },

        _renderMenu: function () {
            var self = this;

            var menu = $("<ul />", {
                "class": "tour-launcher-menu " + (
                    this.options.config.launcher_position === "bottom-left"
                        ? "tour-launcher-menu--bottom-left"
                        : "tour-launcher-menu--bottom-right"
                ),
                role: "menu"
            }).hide();

            this.tours.forEach(function (tour) {
                var item = $("<li />", { role: "none" });
                var link = $("<button />", {
                    type: "button",
                    role: "menuitem",
                    text: tour.title || self._("Untitled tour"),
                    "class": "tour-launcher-menu__item",
                });

                link.on("click", function () {
                    self._hideMenu();
                    self._startTour(tour);
                });

                item.append(link);
                menu.append(item);
            });

            return menu;
        },

        _toggleMenu: function () {
            if (this.menu.is(":visible")) {
                this._hideMenu();
            } else {
                this.menu.show();
                this.launcher.attr("aria-expanded", "true");
            }
        },

        _hideMenu: function () {
            if (this.menu) {
                this.menu.hide();
                this.launcher.attr("aria-expanded", "false");
            }
        },

        _closeMenuOnOutsideClick: function (e) {
            if (!this.menu?.is(":visible")) {
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

                if (this._getSeen(tour.id)) {
                    continue;
                }

                this._setSeen(tour.id);
                this._startTour(tour);
                return;
            }
        },

        _getSeen: function (tourId) {
            try {
                return window.localStorage.getItem(this._seenKey(tourId));
            } catch (e) {
                return null;
            }
        },

        _setSeen: function (tourId) {
            try {
                window.localStorage.setItem(this._seenKey(tourId), "1");
            } catch (e) {
                // private mode / storage disabled — auto-start will just repeat
            }
        },

        _startTour: function (tour) {
            this._setSeen(tour.id);
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

            // a step can be re-shown (back/forward), so drop any stale bullets
            // this step's popup already carries before rebuilding them
            document.querySelectorAll(".shepherd-stats").forEach(function (el) {
                el.remove();
            });

            var progressListEl = document.createElement('ul');
            progressListEl.className = "list-unstyled shepherd-stats";

            for (var i = 0; i < tour.steps.length; i++) {
                var bulletElement = document.createElement('li');
                bulletElement.innerText = " ";
                bulletElement.dataset.stepId = tour.steps[i].id;

                if (i === currentStepIdx) {
                    bulletElement.className = "active";
                }

                bulletElement.addEventListener("click", function (e) {
                    tour.show(e.target.dataset.stepId);
                });

                progressListEl.appendChild(bulletElement);
            }

            var footer = document.querySelector(".shepherd-footer");
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

            steps.forEach(function (step, idx) {
                var isLast = steps.length - 1 === idx;
                var isFirst = idx === 0;
                var lastButtonText = isLast ? self._("Done") : "→";
                var firstButtonClasses = isFirst ? 'shepherd-back disabled' : 'shepherd-back';

                if (step.image_url) {
                    var imageData = $("<img />", { src: step.image_url })[0].outerHTML;
                    step.text = (step.intro || "") + "<br><br>" + imageData;
                } else {
                    step.text = step.intro || "";
                }

                step.buttons = [
                    {
                        action: function () { return this.back(); },
                        classes: firstButtonClasses,
                        text: "←"
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

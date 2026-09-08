this.ckan.module('tour-init', function (jQuery) {
    return {
        options: {
            template: [
                '<a id="intro-switch" href="#" class="mx-2 question"><i class="fa fa-lg fa-question-circle"></i></a>',
                '<i class="icon-question-sign"></i>',
                '</i>',
                '</a>'
            ].join('\n'),
            config: {
                autoplay: false,
                default_anchor: ".breadcrumb .active"
            }
        },

        initialize: function () {
            $.proxyAll(this, /_/);

            this.tour = null;
            this.isMobile = this._isMobile()

            $.ajax({
                url: this.sandbox.url("/api/action/tour_list"),
                // only active tours, and only the fields this widget reads
                // (fl is repeated per field, like package_search)
                data: { state: "active", fl: ["id", "state", "anchor", "page", "steps"] },
                traditional: true,
                cache: false,
                success: this._onSuccessRequest,
            });
        },

        _isMobile: function () {
            // Autoplay is suppressed on small/touch screens where the Shepherd
            // popup positioning and body-scroll-lock behave poorly. A media
            // query covers this.
            if (!window.matchMedia) {
                return false;
            }

            return window.matchMedia("(max-width: 768px), (pointer: coarse)").matches;
        },

        /**
         * Return `selector` only if it is a string that a browser can use as a
         * CSS selector; otherwise null. Guards against `anchor` / `element`
         * values that jQuery would parse as HTML (`<...>`) or that are not
         * valid selector syntax (which would otherwise throw and abort the tour).
         *
         * @param {*} selector
         * @returns {string|null}
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

        /**
         * Creates a tour mark if not exist
         *
         * @returns
         */
        createMark: function () {
            if (!this.mark) {
                this.mark = jQuery(this.options.template);
            }
            return this.mark;
        },

        _onSuccessRequest: function (data) {
            data.result.forEach(element => this._initIntro(element));
        },

        _initIntro: function (introData) {
            var isActive = introData.state === "active";
            var showed = localStorage.getItem('intro-' + introData.id);

            var shouldAttach = isActive && !introData.page;
            var shouldStart = isActive && !showed && !this.isMobile && window.location.pathname == introData.page;
            var anchorSelector = this._safeSelector(introData.anchor);
            var anchorExists = anchorSelector && document.querySelector(anchorSelector) !== null;

            this.tour = new Shepherd.Tour({
                useModalOverlay: true,
                defaultStepOptions: {
                    floatingUIOptions: { middleware: [FloatingUICore.offset(20)] },
                    cancelIcon: {
                        enabled: true,
                        label: "Skip tour"
                    },
                    modalOverlayOpeningPadding: 5,
                    modalOverlayOpeningRadius: 5,
                    classes: 'tour-step',
                    scrollTo: { behavior: 'smooth', block: 'center' },
                    when: {
                        show() {
                            // prevent scrolling while we are showing tour
                            bodyScrollLock.disableBodyScroll(".tour-step");

                            const currentStep = this;
                            const currentStepIdx = this.tour.steps.indexOf(currentStep);

                            const progressListEl = document.createElement('ul');
                            progressListEl.classList = ["list-unstyled shepherd-stats"]

                            for (let i = 0; i < this.tour.steps.length; i++) {
                                const bulletElement = document.createElement('li');
                                bulletElement.innerText = " ";
                                bulletElement.dataset.stepId = this.tour.steps[i].id;

                                if (i === currentStepIdx) {
                                    bulletElement.classList = ["active"];
                                }

                                $(bulletElement).click((el) => {
                                    Shepherd.activeTour.show(el.target.dataset.stepId);
                                })

                                progressListEl.append(bulletElement)
                            }

                            $('.shepherd-footer').before(progressListEl);
                        },
                        destroy() {
                            // release scroll after tour
                            bodyScrollLock.clearAllBodyScrollLocks();
                        }
                    }
                },

            });

            this.tour.addSteps(this._prepareSteps(introData.steps));

            if (shouldAttach) {
                this.createMark();

                var target = anchorExists
                    ? anchorSelector
                    : this._safeSelector(this.options.config.default_anchor);

                if (target) {
                    this.mark.insertAfter(target);
                }

                this.mark.on('click', this._onClick);
            }

            if (shouldStart && this.options.config.autoplay) {
                localStorage.setItem('intro-' + introData.id, 1);
                this.tour.start();
            }
        },

        _prepareSteps: function (steps) {
            steps.forEach((step, idx) => {
                let isLast = steps.length - 1 === idx;
                let isFirst = idx === 0;
                let lastButtonText = isLast ? this._("Done") : "→";
                let firstButtonClasses = isFirst ? 'shepherd-back disabled' : 'shepherd-back';

                if (step.image_url) {
                    const imageData = $("<img />", {src: step.image_url})[0].outerHTML;
                    step.text = step.intro + "<br><br>" + imageData;
                } else {
                    step.text = step.intro;
                }

                step.buttons = [
                    {
                        action() {
                            return this.back();
                        },
                        classes: firstButtonClasses,
                        text: "←"
                    },
                    {
                        action() {
                            return this.next();
                        },
                        classes: 'shepherd-next',
                        text: lastButtonText
                    }
                ]

                var stepSelector = this._safeSelector(step.element);
                if (stepSelector) {
                    step.attachTo = {
                        element: stepSelector,
                        on: step.position
                    };
                }
                // an unsafe/invalid selector leaves the step unattached, so
                // Shepherd renders it as a centered modal instead of throwing
            });

            return steps;
        },

        _onClick: function (e) {
            this.tour.start();
        }
    }
});

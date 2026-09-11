/**
 * A script to manage multiple steps fieldsets
 */
ckan.module("tour-steps", function ($) {
    return {
        initialize: function () {
            $.proxyAll(this, /_on/);
            var self = this;

            // this vars
            this.addStepBtn = $(".add-step");

            // add event listeners
            $(document).on('click', '.btn-collapse-steps', this._onCollapseAllSteps);

            // An unsaved step (just added, never sent to the server) has no
            // hx-post on its remove button -- see tour_step.html -- since
            // there's nothing server-side to delete. Still confirm: the user
            // may have already typed real content into it. Remove it
            // client-side only, with no server round-trip.
            $(document).on('click', '.remove-step:not([hx-post])', function (e) {
                var stepId = $(e.currentTarget).data('step-id');

                self._confirmStepDeletion(function () {
                    self._onRemoveStep(stepId);
                });
            });

            // HTMX events
            document.body.addEventListener('htmx:afterSwap', function (e) {
                let requestPath = e.detail.pathInfo.requestPath;

                if (requestPath.endsWith("/add_step")) {
                    self._toggleRemoveBtns();
                    self._updateStepsIndexes();
                    self._initStepModules(e.detail.elt);
                }
            });

            this._toggleRemoveBtns();
            this._updateStepsIndexes();

            new Sortable.default(document.querySelectorAll('.tour-steps__steps'), {
                draggable: '.tour-accordion',
                handle: ".dragger",
                sortAnimation: {
                    duration: 200,
                    easingFunction: 'ease-in-out',
                },
                plugins: [Plugins.SortAnimation]
            }).on('drag:stopped', () => this._updateStepsIndexes())


            document.body.addEventListener('htmx:confirm', function (evt) {
                if (evt.detail.path.includes("/tour/delete_step")) {
                    evt.preventDefault();

                    self._confirmStepDeletion(function () {
                        evt.detail.issueRequest();
                    });
                }
            });

            document.body.addEventListener('htmx:afterRequest', function (evt) {
                var requestPath = evt.detail.pathInfo && evt.detail.pathInfo.requestPath;

                if (!requestPath || !requestPath.includes("/tour/delete_step")) {
                    return;
                }

                var stepId = evt.detail.elt.dataset.stepId;

                if (evt.detail.successful) {
                    self._onRemoveStep(stepId);
                } else {
                    var reason = (evt.detail.xhr && evt.detail.xhr.responseText || "").trim()
                        || "Could not delete step. Please reload the page and try again.";

                    ckan.notify(reason, "", "error");
                }
            });
        },

        /**
         * Shared "are you sure" prompt for removing a step, whether or not
         * it's been saved yet -- the user may have already typed real
         * content into it either way.
         *
         * @param {Function} onConfirm
         */
        _confirmStepDeletion: function (onConfirm) {
            ckan.confirm({
                message: "Are you sure you wish to delete a step?",
                title: "Confirm deletion",
                icon: "<i class='fa fa-trash me-2'></i>",
                confirmText: "Delete",
                type: "danger",
                onConfirm: onConfirm,
            });
        },

        /**
         * Remove a step node from DOM
         *
         * @param {string} e
         */
        _onRemoveStep: function (stepId) {
            var self = this;

            $("#step-" + stepId).hide('slow', function () {
                this.remove();
                self._toggleRemoveBtns();
                self._updateStepsIndexes();
            });
        },

        /**
         * Should be at least 1 step for a tour. Disable remove step button if
         * only 1 left.
         */
        _toggleRemoveBtns: function () {
            var steps = $(".tour-steps__steps .tour-accordion");
            $(".remove-step").toggleClass("disabled", steps.length == 1)
        },

        /**
         * Initialize data-module elements inside a step just added
         * over htmx, plus anything main.js otherwise only wires up once,
         * on page load -- Bootstrap popovers being the one this form uses.
         */
        _initStepModules: function (elt) {
            if (!elt || !elt.querySelectorAll) {
                return;
            }

            elt.querySelectorAll("[data-module]").forEach(function (node) {
                if (!node.getAttribute("dm-initialized")) {
                    ckan.module.initializeElement(node);
                    node.setAttribute("dm-initialized", true);
                }
            });

            if ($.fn.popover !== undefined) {
                $(elt).find('[data-bs-toggle="popover"]').popover();
            }
        },

        /**
         * Update the steps indexes on sorting or adding a new one
         */
        _updateStepsIndexes: function () {
            var steps = $(".tour-steps__steps .tour-accordion")
                .not(".draggable-source--is-dragging")
                .not(".draggable--original");

            steps.each((idx, step) => this._updateStepIndexes(idx + 1, step));
        },

        /**
         * Update a specific step indexes
         *  - update accordion header
         *  - update a hidden field we are sending to the server
         *
         * @param {HTMLElement} step
         */
        _updateStepIndexes: function (idx, step) {
            $(step).find(".step-number").text(idx);
            // step fields are namespaced as step[<id>][index]
            $(step).find("input[name$='[index]']").val(idx);
        },

        _onCollapseAllSteps: function (e) {
            e.preventDefault();

            if ($('.btn-collapse-steps').attr("collapsed") == 1) {
                $(".tour-steps__steps .accordion-collapse").collapse("show");

                $('.btn-collapse-steps').text("Collapse all steps");
                $('.btn-collapse-steps').attr("collapsed", 0);
            } else {
                $(".tour-steps__steps .accordion-collapse").collapse("hide");

                $('.btn-collapse-steps').text("Expand all steps");
                $('.btn-collapse-steps').attr("collapsed", 1);
            }
        }
    };
});

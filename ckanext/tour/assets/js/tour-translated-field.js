/**
 * Lets a title/intro field start with only the default locale's input and
 * add one row for each locale the user selects via "+ Add language".
*/
ckan.module("tour-translated-field", function ($) {
    return {
        options: {
            name: "",
            kind: "input"
        },

        initialize: function () {
            $.proxyAll(this, /_on/);

            this.rows = this.el.find(".tour-translated-field__rows");
            this.picker = this.el.find(".tour-translated-field__picker");

            this.picker.on("change", this._onAdd);
            this.el.on("click", ".tour-translated-field__remove", this._onRemove);
        },

        _onAdd: function () {
            var code = this.picker.val();

            if (!code) {
                return;
            }

            var option = this.picker.find('option[value="' + code + '"]');
            var label = option.text();

            option.remove();
            // .val() alone doesn't update select2's own display -- trigger()
            // does, and is safe to re-enter since _onAdd bails out on the
            // now-empty value.
            this.picker.val("").trigger("change");

            this._addRow(code, label);
        },

        _addRow: function (code, label) {
            var fieldName = this.options.name + "[" + code + "]";
            var fieldId = "field-" + fieldName.replace(/[[\]]/g, "-");

            var field = this.options.kind === "markdown"
                ? $("<textarea>", {id: fieldId, name: fieldName, "class": "form-control", rows: 5})
                : $("<input>", {id: fieldId, name: fieldName, type: "text", "class": "form-control"});

            var removeBtn = $("<button>", {
                type: "button",
                "class": "btn btn-sm btn-link tour-translated-field__remove",
                text: this._("Remove")
            }).attr({"data-locale-code": code, "data-locale-label": label});

            var row = $("<div>", {"class": "form-group tour-translated-field__row"})
                .append($("<label>", {"class": "form-label", "for": fieldId, text: label}))
                .append($("<div>", {"class": "controls"}).append(field).append(removeBtn));

            this.rows.append(row);
            field.trigger("focus");
        },

        _onRemove: function (e) {
            var btn = $(e.currentTarget);
            var code = btn.data("locale-code");
            var label = btn.data("locale-label");

            btn.closest(".tour-translated-field__row").remove();

            if (code) {
                this._ensurePicker().append($("<option>", {value: code, text: label}));
            }
        },

        /**
         * Every locale can end up shown at once (nothing left to add), so the
         * picker is omitted server-side -- build it on first use instead of
         * silently dropping a locale freed up by a later removal.
         */
        _ensurePicker: function () {
            if (!this.picker.length) {
                var pickerId = "field-" + (this.options.name + "-add-language").replace(/[[\]]/g, "-");

                this.picker = $("<select>", {
                    id: pickerId,
                    name: pickerId,
                    "class": "form-select form-select-sm tour-translated-field__picker",
                    "data-module": "autocomplete"
                })
                    .attr("aria-label", this._("Add a language"))
                    .append($("<option>", {value: "", text: this._("+ Add language")}))
                    .appendTo(this.el)
                    .on("change", this._onAdd);

                // built at runtime, so it missed the page-load module scan
                ckan.module.initializeElement(this.picker[0]);
            }

            return this.picker;
        }
    };
});

Vue.component('summerNote', {
    props: ['value', 'placeholder'],
    render: function (h) {
        return h('div', {
            attrs: {
                id: 'editor',
            },
            domProps: {
                innerHTML: this.value
            }
        })
    },
    data: function () {
        return {
            tabsize: 2,
            height: 280
        }
    },
    methods: {
        change: function (contents, $editable) {
            this.$emit('input', contents)
        }
    },
    mounted: function () {
        $("div#editor").summernote({
            placeholder: this.placeholder,
            tabsize: this.tabsize,
            height: this.height,
            callbacks: {
                onChange: this.change
            }
        });
    }
})

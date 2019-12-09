from django import forms


class MultipleFileFieldForm(forms.Form):
    file_field = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}))


class JsonFileForm(forms.Form):
    json_file = forms.FileField()

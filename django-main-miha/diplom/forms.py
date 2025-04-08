from django import forms
from django.forms import ModelForm, TextInput, NumberInput, Select

class JournalForm(forms.Form):
    div_no = forms.IntegerField(label='Цех', widget=forms.NumberInput(attrs={'class':'form-control'})) # 'Цех'
    num_punct = forms.IntegerField(label='Номер пункта разрешения', widget=forms.NumberInput(attrs={'class':'form-control'})) # Номер пункта разрешения' 
    num_sp = forms.CharField(label='№ СП', widget=forms.TextInput(attrs={'class':'form-control'})) # N СП' 
    pmd_material = forms.CharField(label='Материал ТП', widget=forms.TextInput(attrs={'class':'form-control'})) # 'Материал ТП
    pmd_note_tp = forms.CharField(label='Документ разрешающий запуск материала', widget=forms.TextInput(attrs={'class':'form-control'})) # 
    pmd_note_pi = forms.CharField(label='Примечание ПИ',widget=forms.TextInput(attrs={'class':'form-control'})) # 'Примечание ПИ
    ul_login = forms.CharField(label='Ответственный за паспорт', widget=forms.TextInput(attrs={'class':'form-control'})) # Ответсвенный за паспорт
    pmd_responsible = forms.CharField(label='Ответственный за материал', widget=forms.TextInput(attrs={'class':'form-control'})) # 'Ответсвенный за материал
    

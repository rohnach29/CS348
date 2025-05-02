from django import forms
from .models import Run, Route, Comment
from django.core.exceptions import ValidationError
from datetime import timedelta

class DurationWidget(forms.widgets.TextInput):
    def format_value(self, value):
        if value is None or value == '':
            return ''
        
        # If it's already a string, return it
        if isinstance(value, str):
            return value
            
        # If it's a timedelta object
        if isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
        return str(value)

class RunForm(forms.ModelForm):
    duration = forms.CharField(
        widget=DurationWidget(attrs={'placeholder': 'HH:MM:SS'}),
        help_text="Enter duration in HH:MM:SS format"
    )
    
    class Meta:
        model = Run
        fields = [
            'title', 'date', 'start_time', 'duration', 'distance_km', 
            'route', 'calories_burned', 'average_heart_rate', 
            'weather_conditions', 'temperature_c', 'notes', 'is_public'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean_duration(self):
        duration_str = self.cleaned_data.get('duration')
        try:
            # Parse the duration string (HH:MM:SS)
            hours, minutes, seconds = map(int, duration_str.split(':'))
            duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            return duration
        except ValueError:
            raise ValidationError("Invalid duration format. Please use HH:MM:SS.")

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = [
            'name', 'start_location', 'end_location', 
            'distance_km', 'elevation_gain_m', 'description'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Leave a comment...'}),
        }

class RunFilterForm(forms.Form):
    """Form for filtering runs in reports."""
    start_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    min_distance = forms.DecimalField(
        required=False, 
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'Min distance (km)'})
    )
    max_distance = forms.DecimalField(
        required=False, 
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'Max distance (km)'})
    )
    route = forms.ModelChoiceField(
        queryset=Route.objects.all(),
        required=False,
        empty_label="Any route"
    ) 
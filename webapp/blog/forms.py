from flask_wtf import FlaskForm as Form
from wtforms import StringField, TextAreaField, DateTimeField, EmailField
from wtforms.validators import DataRequired, Length


class TagListField(StringField):
    """Stringfield for a list of separated tags"""

    def __init__(self, label='', validators=None, remove_duplicates=True, to_lowercase=False, separator=' ', **kwargs):
        """
        Construct a new field.
        :param label: The label of the field.
        :param validators: A sequence of validators to call when validate is called.
        :param remove_duplicates: Remove duplicates in a case insensitive manner.
        :param to_lowercase: Cast all values to lowercase.
        :param separator: The separator that splits the individual tags.
        """
        super(TagListField, self).__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates
        self.to_lowercase = to_lowercase
        self.separator = separator
        
    def _value(self):
        if self.data:
            return u', '.join(self.data)
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(self.separator)]
            if self.remove_duplicates:
                self.data = list(self._remove_duplicates(self.data))
            if self.to_lowercase:
                self.data = [x.lower() for x in self.data]

    @classmethod
    def _remove_duplicates(cls, seq):
        """Remove duplicates in a case insensitive, but case preserving manner"""
        d = {}
        for item in seq:
            if item.lower() not in d:
                d[item.lower()] = True
                yield item


class CommentForm(Form):
    name = StringField(
        'Name',
        validators=[DataRequired(), Length(max=255)]
    )
    text = TextAreaField(u'Comment', validators=[DataRequired()])


class PostForm(Form):
    title = StringField('Title', [
        DataRequired(),
        Length(max=255)
    ])
    youtube_id = StringField('Youtube video id', [Length(max=255)])
    text = TextAreaField('Content', [DataRequired()])
    tags = TagListField(
        "Tags",
        separator=",",
        validators=[Length(max=100, message="You can only use up to 100 characters.")]
    )


class ReminderForm(Form):
    email = EmailField(
        'Email',
        validators=[DataRequired()]
    )
    text = TextAreaField(u'Comment', validators=[DataRequired()])

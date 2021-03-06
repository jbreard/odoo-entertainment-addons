# © 2019 - today Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

SOUND = 'sound'
VIDEO = 'video'
GROUP = 'group'


RECORDING_TYPES = (
    (SOUND, 'Sound'),
    (VIDEO, 'Video'),
    (GROUP, 'Group of Recordings'),
)


class Recording(models.Model):

    _name = 'recording'
    _description = 'Recording'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, string="Title")
    active = fields.Boolean(default=True)

    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda s: s.env.user.company_id
    )

    ttype = fields.Selection(
        RECORDING_TYPES,
        string='Type of Recording',
        required=True,
    )

    duration = fields.Float()

    production_start_date = fields.Date()
    release_date = fields.Date()

    publication_country_id = fields.Many2one(
        'res.country',
        string='Place of Publication',
    )

    note = fields.Text()


class RecordingSound(models.Model):

    _inherit = 'recording'

    related_video_count = fields.Integer(
        compute='_compute_related_video_count'
    )

    def _compute_related_video_count(self):
        for rec in self:
            rec.related_video_count = self.env['recording'].search([
                ('sound_recording_id', '=', rec.id),
                ('ttype', '=', 'video'),
            ], count=True)


class RecordingVideo(models.Model):

    _inherit = 'recording'

    sound_recording_id = fields.Many2one('recording')
    filming_location = fields.Char()


class RecordingGroup(models.Model):

    _inherit = 'recording'

    group_type = fields.Selection([
        ('album', 'Album'),
        ('ep', 'EP'),
        ('single', 'Single'),
        ('compilation', 'Compilation'),
        ('split', 'Split'),
    ])

    track_ids = fields.One2many(
        'recording.track', 'recording_group_id', 'Related Recordings',
    )

    number_of_tracks = fields.Integer(
        string="Total Number of Tracks",
        compute='_compute_number_of_tracks'
    )

    def _compute_number_of_tracks(self):
        for rec in self:
            rec.number_of_tracks = len(rec.track_ids)

    group_duration = fields.Float(
        string="Group Duration",
        compute='_compute_group_duration',
        store=True,
    )

    @api.depends('track_ids.recording_id.duration')
    def _compute_group_duration(self):
        for rec in self:
            rec.group_duration = sum(t.recording_id.duration for t in rec.track_ids)

    next_volume_number = fields.Char(
        compute='_compute_next_track_values'
    )

    next_track_number = fields.Char(
        compute='_compute_next_track_values'
    )

    @api.depends('track_ids.track', 'track_ids.volume')
    def _compute_next_track_values(self):
        recordings_with_tracks = self.filtered(lambda r: r.track_ids)
        recordings_without_tracks = self - recordings_with_tracks

        for rec in recordings_with_tracks:
            last_track = rec.track_ids[-1]

            rec.next_volume_number = last_track.volume

            last_track_number = (rec.track_ids[-1].track or '').strip()
            if last_track_number.isdigit():
                rec.next_track_number = str(int(last_track_number) + 1)

        for rec in recordings_without_tracks:
            rec.next_volume_number = '1'
            rec.next_track_number = '1'

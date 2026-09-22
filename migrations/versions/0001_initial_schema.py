"""Initial schema.

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa
revision, down_revision, branch_labels, depends_on = '0001', None, None, None
def upgrade():
    op.create_table('users', sa.Column('id',sa.Integer,primary_key=True), sa.Column('full_name',sa.String(160),nullable=False), sa.Column('username',sa.String(64),nullable=False,unique=True), sa.Column('email',sa.String(254),nullable=False,unique=True), sa.Column('password_hash',sa.String(512),nullable=False), sa.Column('role',sa.String(16),nullable=False), sa.Column('is_active',sa.Boolean,nullable=False), sa.Column('must_change_password',sa.Boolean,nullable=False), sa.Column('created_at',sa.DateTime(timezone=True),nullable=False), sa.Column('last_login_at',sa.DateTime(timezone=True)))
    op.create_table('model_versions', sa.Column('id',sa.Integer,primary_key=True),sa.Column('identifier',sa.String(128),nullable=False,unique=True),sa.Column('description',sa.Text,nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('experiments',sa.Column('id',sa.Integer,primary_key=True),sa.Column('user_id',sa.Integer,sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),sa.Column('submitted_at',sa.DateTime(timezone=True),nullable=False),sa.Column('status',sa.String(24),nullable=False),sa.Column('image_path',sa.String(512)),sa.Column('processing_ms',sa.Integer))
    op.create_table('image_validation_results',sa.Column('id',sa.Integer,primary_key=True),sa.Column('experiment_id',sa.Integer,sa.ForeignKey('experiments.id',ondelete='CASCADE'),nullable=False,unique=True),sa.Column('is_valid',sa.Boolean,nullable=False),sa.Column('is_fish',sa.Boolean,nullable=False),sa.Column('confidence',sa.Float,nullable=False),sa.Column('detected_label',sa.String(128),nullable=False),sa.Column('reason',sa.Text,nullable=False),sa.Column('status',sa.String(24),nullable=False))
    op.create_table('prediction_results',sa.Column('id',sa.Integer,primary_key=True),sa.Column('experiment_id',sa.Integer,sa.ForeignKey('experiments.id',ondelete='CASCADE'),nullable=False,unique=True),sa.Column('model_version_id',sa.Integer,sa.ForeignKey('model_versions.id'),nullable=False),sa.Column('growth_stage',sa.String(32),nullable=False),sa.Column('confidence',sa.Float,nullable=False),sa.Column('probabilities_json',sa.Text,nullable=False),sa.Column('standard_length_cm',sa.Float,nullable=False),sa.Column('total_length_cm',sa.Float,nullable=False),sa.Column('weight_g',sa.Float,nullable=False))
    op.create_table('admin_audit_logs',sa.Column('id',sa.Integer,primary_key=True),sa.Column('admin_user_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False),sa.Column('action',sa.String(96),nullable=False),sa.Column('target_type',sa.String(48),nullable=False),sa.Column('target_id',sa.String(64),nullable=False),sa.Column('details',sa.Text),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
def downgrade():
    for table in ('admin_audit_logs','prediction_results','image_validation_results','experiments','model_versions','users'): op.drop_table(table)

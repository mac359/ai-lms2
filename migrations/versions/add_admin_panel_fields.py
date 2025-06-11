"""Add admin panel fields

Revision ID: add_admin_panel_fields
Revises: add_student_feedback_summary_to_instructor_profile
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_admin_panel_fields'
down_revision = 'add_student_feedback_summary_to_instructor_profile'
branch_labels = None
depends_on = None

def upgrade():
    # Add fields to User table
    op.add_column('user', sa.Column('last_login', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('login_count', sa.Integer(), nullable=True, default=0))
    
    # Add fields to StudentProfile table
    op.add_column('student_profile', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('student_profile', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('student_profile', sa.Column('student_id', sa.String(length=50), nullable=True))
    op.add_column('student_profile', sa.Column('parent_email', sa.String(length=120), nullable=True))
    op.add_column('student_profile', sa.Column('parent_phone', sa.String(length=20), nullable=True))
    
    # Add fields to InstructorProfile table
    op.add_column('instructor_profile', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('instructor_profile', sa.Column('department', sa.String(length=100), nullable=True))
    op.add_column('instructor_profile', sa.Column('office_location', sa.String(length=100), nullable=True))
    op.add_column('instructor_profile', sa.Column('office_hours', sa.String(length=100), nullable=True))
    op.add_column('instructor_profile', sa.Column('specialization', sa.String(length=200), nullable=True))
    
    # Add fields to Course table
    op.add_column('course', sa.Column('code', sa.String(length=20), nullable=True))
    op.add_column('course', sa.Column('category', sa.String(length=50), nullable=True))
    op.add_column('course', sa.Column('level', sa.String(length=20), nullable=True))
    op.add_column('course', sa.Column('max_students', sa.Integer(), nullable=True, default=50))
    op.add_column('course', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('course', sa.Column('end_date', sa.Date(), nullable=True))
    op.add_column('course', sa.Column('meeting_days', sa.String(length=100), nullable=True))
    op.add_column('course', sa.Column('meeting_time', sa.Time(), nullable=True))
    op.add_column('course', sa.Column('syllabus', sa.Text(), nullable=True))
    op.add_column('course', sa.Column('prerequisites', sa.Text(), nullable=True))
    op.add_column('course', sa.Column('learning_outcomes', sa.Text(), nullable=True))
    op.add_column('course', sa.Column('is_active', sa.Boolean(), nullable=True, default=True))
    op.add_column('course', sa.Column('allow_enrollment', sa.Boolean(), nullable=True, default=True))
    op.add_column('course', sa.Column('enable_quizzes', sa.Boolean(), nullable=True, default=True))
    op.add_column('course', sa.Column('enable_assignments', sa.Boolean(), nullable=True, default=True))
    
    # Add fields to Assignment table
    op.add_column('assignment', sa.Column('is_active', sa.Boolean(), nullable=True, default=True))
    
    # Add fields to Quiz table
    op.add_column('quiz', sa.Column('is_active', sa.Boolean(), nullable=True, default=True))
    
    # Create AssignmentSubmission table
    op.create_table('assignment_submission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=True),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('grade', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Material table
    op.create_table('material',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Remove Material table
    op.drop_table('material')
    
    # Remove AssignmentSubmission table
    op.drop_table('assignment_submission')
    
    # Remove fields from Quiz table
    op.drop_column('quiz', 'is_active')
    
    # Remove fields from Assignment table
    op.drop_column('assignment', 'is_active')
    
    # Remove fields from Course table
    op.drop_column('course', 'enable_assignments')
    op.drop_column('course', 'enable_quizzes')
    op.drop_column('course', 'allow_enrollment')
    op.drop_column('course', 'is_active')
    op.drop_column('course', 'learning_outcomes')
    op.drop_column('course', 'prerequisites')
    op.drop_column('course', 'syllabus')
    op.drop_column('course', 'meeting_time')
    op.drop_column('course', 'meeting_days')
    op.drop_column('course', 'end_date')
    op.drop_column('course', 'start_date')
    op.drop_column('course', 'max_students')
    op.drop_column('course', 'level')
    op.drop_column('course', 'category')
    op.drop_column('course', 'code')
    
    # Remove fields from InstructorProfile table
    op.drop_column('instructor_profile', 'specialization')
    op.drop_column('instructor_profile', 'office_hours')
    op.drop_column('instructor_profile', 'office_location')
    op.drop_column('instructor_profile', 'department')
    op.drop_column('instructor_profile', 'phone')
    
    # Remove fields from StudentProfile table
    op.drop_column('student_profile', 'parent_phone')
    op.drop_column('student_profile', 'parent_email')
    op.drop_column('student_profile', 'student_id')
    op.drop_column('student_profile', 'bio')
    op.drop_column('student_profile', 'phone')
    
    # Remove fields from User table
    op.drop_column('user', 'login_count')
    op.drop_column('user', 'last_login') 
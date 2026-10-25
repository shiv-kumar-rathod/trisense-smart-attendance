class ReportService:
    """Week 4 reporting boundary.

    Planned outputs:
    daily, monthly, subject-wise and student-wise reports,
    Excel export and PDF export.
    """

    def export_excel(self, rows, output_path):
        raise NotImplementedError("Implement during Week 4.")

    def export_pdf(self, rows, output_path):
        raise NotImplementedError("Implement during Week 4.")

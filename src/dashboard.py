class Dashboard:

    def __init__(self, filter_period=None):
        self.filter_period = filter_period
        self.performance_metrics = {}
        self.charts = {}
        self.retrieved_data = []

    def calculate_analytics(self):
        # Calculates performance analytics from retrieved data
        if not self.retrieved_data:
            self.performance_metrics = {}
            return self.performance_metrics

        bookings = self.retrieved_data.get('bookings', [])
        employees = self.retrieved_data.get('employees', [])
        customers = self.retrieved_data.get('customers', [])
        services  = self.retrieved_data.get('services', [])

        total = len(bookings)
        completed = sum(1 for b in bookings if b.booking_status == 'completed')
        cancelled = sum(1 for b in bookings if b.booking_status == 'cancelled')
        confirmed = sum(1 for b in bookings if b.booking_status == 'confirmed')
        pending   = sum(1 for b in bookings if b.booking_status == 'pending')

        self.performance_metrics = {
            'total_bookings': total,
            'completed_bookings': completed,
            'cancelled_bookings': cancelled,
            'confirmed_bookings': confirmed,
            'pending_bookings': pending,
            'completion_rate': round((completed / total * 100), 2) if total > 0 else 0,
            'cancellation_rate': round((cancelled / total * 100), 2) if total > 0 else 0,
            'total_employees': len(employees),
            'total_customers': len(customers),
            'total_services': len(services),
        }
        return self.performance_metrics

    def format_charts(self):
        # Formats performance metrics into chart-ready structures
        if not self.performance_metrics:
            self.calculate_analytics()

        self.charts = {
            'booking_status_breakdown': {
                'type': 'pie',
                'labels': ['Completed', 'Cancelled', 'Confirmed', 'Pending'],
                'values': [
                    self.performance_metrics.get('completed_bookings', 0),
                    self.performance_metrics.get('cancelled_bookings', 0),
                    self.performance_metrics.get('confirmed_bookings', 0),
                    self.performance_metrics.get('pending_bookings', 0),
                ],
            },
            'completion_vs_cancellation': {
                'type': 'bar',
                'labels': ['Completion Rate', 'Cancellation Rate'],
                'values': [
                    self.performance_metrics.get('completion_rate', 0),
                    self.performance_metrics.get('cancellation_rate', 0),
                ],
            },
        }
        return self.charts

    def apply_filter(self, periodID):
        # Filters dashboard data by work week
        self.filter_period = periodID
        if isinstance(self.retrieved_data, dict):
            bookings = self.retrieved_data.get('bookings', [])
            filtered = [b for b in bookings if b.periodID == periodID]
            self.retrieved_data['bookings'] = filtered

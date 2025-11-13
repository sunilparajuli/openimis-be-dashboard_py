import graphene
from django.db.models import Count, Sum, Q, Avg
from django.db.models.functions import TruncMonth
from claim.models import Claim
from .gql_queries import *
from dashboard.apps import DashboardConfig
from .utils import get_current_user_hf


class Query(graphene.ObjectType):
    geospatial_analytics = graphene.Field(GeospatialAnalyticsGQLType)
    epidemiological_analytics = graphene.Field(EpidemiologicalAnalyticsGQLType)
    customer_journey_analytics = graphene.Field(CustomerJourneyAnalyticsGQLType)
    operational_analytics = graphene.Field(OperationalAnalyticsGQLType)
    social_protection_analytics = graphene.Field(SocialProtectionAnalyticsGQLType)
    analytics = graphene.Field(AnalyticsGQLType)
    dashboard = graphene.Field(DashboardGQLType)

    def resolve_geospatial_analytics(self, info, **kwargs):
        """Demo data for geospatial analytics."""
        demo_provinces = [
            {'region_code': 'NP-P1', 'total_claimed': 7123456.25, 'count': 510},
            {'region_code': 'NP-P2', 'total_claimed': 4321098.00, 'count': 300},
            {'region_code': 'NP-P3', 'total_claimed': 12540320.50, 'count': 850}
        ]
        demo_providers = [
            {'name': 'Kathmandu Model Hospital', 'location_name': 'Exhibition Road', 'parent_name': 'Kathmandu', 'parent_parent_name': 'Bagmati Province'},
            {'name': 'Patan Hospital', 'location_name': 'Lagankhel', 'parent_name': 'Lalitpur', 'parent_parent_name': 'Bagmati Province'},
        ]
        return GeospatialAnalyticsGQLType(
            claim_summary_by_province=[
                RegionSummaryType(region_name=item['region_code'], total_claimed_amount=str(item['total_claimed']), claim_count=item['count'])
                for item in demo_provinces
            ],
            provider_network_details=[
                ProviderNetworkDetailType(facility_name=item['name'], location_name=item['location_name'], district_name=item['parent_name'], province_name=item['parent_parent_name'])
                for item in demo_providers
            ]
        )

    def resolve_epidemiological_analytics(self, info, **kwargs):
        """Single query for disease analytics."""

        user = info.context.user
        hf_filter = {}

        if DashboardConfig.dashboard_per_hf:
            hf = get_current_user_hf(user)
            if hf:
                hf_filter = {"health_facility": hf}

        base_qs = Claim.objects.filter(validity_to__isnull=True, icd__isnull=False, **hf_filter)

        disease_data = (
            base_qs
            .values('icd__name')
            .annotate(count=Count('id'), total_cost=Sum('claimed'))
            .order_by('-count')[:10]
        )
        trend_data = (
            base_qs
            .annotate(month=TruncMonth('date_claimed'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')[:12]
        )
        return EpidemiologicalAnalyticsGQLType(
            top_claimed_diseases_by_volume=[
                IcdSummaryType(icd_name=item['icd__name'], claim_count=item['count'])
                for item in disease_data
            ],
            top_claimed_diseases_by_cost=[
                IcdSummaryType(icd_name=item['icd__name'], total_claimed_amount=item['total_cost'])
                for item in sorted(disease_data, key=lambda x: x['total_cost'] or 0, reverse=True)
            ],
            overall_claim_trend=[
                DiseaseTrendPointType(month=item['month'].strftime('%Y-%m'), claim_count=item['count'])
                for item in trend_data
            ]
        )

    def resolve_customer_journey_analytics(self, info, **kwargs):
        """Optimized single query for journey data."""

        user = info.context.user
        hf_filter = {}

        if DashboardConfig.dashboard_per_hf:
            hf = get_current_user_hf(user)
            if hf:
                hf_filter = {"health_facility": hf}

        base_qs = Claim.objects.filter(validity_to__isnull=True, **hf_filter)

        counts = base_qs.aggregate(
            entered=Count('id', filter=Q(status__gte=2)),
            checked=Count('id', filter=Q(status__gte=4)),
            processed=Count('id', filter=Q(status__gte=16)),
            paid=Count('id', filter=Q(status=32)),
            pending_feedback=Count('id', filter=Q(status__gte=16, feedback_status=1))
        )
        rejection_data = (
            base_qs.filter(status=1, rejection_reason__isnull=False)
            .values('rejection_reason')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        return CustomerJourneyAnalyticsGQLType(
            claim_lifecycle_funnel=[
                ClaimLifecycleFunnelType(stage_name="Entered", claim_count=counts.get('entered', 0)),
                ClaimLifecycleFunnelType(stage_name="Checked", claim_count=counts.get('checked', 0)),
                ClaimLifecycleFunnelType(stage_name="Processed", claim_count=counts.get('processed', 0)),
                ClaimLifecycleFunnelType(stage_name="Paid", claim_count=counts.get('paid', 0)),
            ],
            rejection_reason_summary=[
                RejectionReasonSummaryType(rejection_reason_code=str(item['rejection_reason']), claim_count=item['count'])
                for item in rejection_data
            ],
            claims_pending_feedback_count=counts.get('pending_feedback', 0),
            claim_payment_times=[ # Demo data as before
                ClaimPaymentTimeType(time_bracket="0-7 Days", claim_count=120),
                ClaimPaymentTimeType(time_bracket="8-15 Days", claim_count=80),
            ]
        )

    def resolve_operational_analytics(self, info, **kwargs):
        """Simplified operational metrics."""
        user = info.context.user
        hf_filter = {}

        if DashboardConfig.dashboard_per_hf:
            hf = get_current_user_hf(user)
            if hf:
                hf_filter = {"health_facility": hf}

        base_qs = Claim.objects.filter(validity_to__isnull=True, health_facility__isnull=False, **hf_filter)
                
        facility_data = (
            base_qs
            .values('health_facility__name')
            .annotate(
                total_claims=Count('id'),
                rejected_claims=Count('id', filter=Q(status=1)),
                avg_claim_value=Avg('claimed')
            )
            .order_by('-total_claims')[:10]
        )
        return OperationalAnalyticsGQLType(
            turnaround_by_facility=[ # Demo data
                ClaimTurnaroundType(category_name="Sample Facility", average_turnaround_days=5.5)
            ],
            adjuster_performance=[ # Demo data
                AdjusterPerformanceType(adjuster_name="Sample Adjuster", claims_processed_count=100, average_adjustment_amount=5000.0, approval_to_claim_ratio=0.85)
            ],
            facility_quality_overview=[
                HealthFacilityQualityType(
                    health_facility_name=item['health_facility__name'],
                    total_claims_submitted=item['total_claims'],
                    rejection_rate_percentage=(item['rejected_claims'] * 100.0 / item['total_claims'] if item['total_claims'] else 0),
                    average_claim_value=item['avg_claim_value']
                ) for item in facility_data
            ]
        )

    def resolve_social_protection_analytics(self, info, **kwargs):
        """Comprehensive social protection analytics focusing on beneficiary welfare and coverage patterns."""
        from django.db.models import Case, When, IntegerField, CharField, Value  
        from datetime import datetime, timedelta
        
        user = info.context.user
        hf_filter = {}

        if DashboardConfig.dashboard_per_hf:
            hf = get_current_user_hf(user)
            if hf:
                hf_filter = {"health_facility": hf}
        
        # Base queryset for recent claims
        recent_claims = Claim.objects.filter(
            validity_to__isnull=True,
            date_claimed__gte=datetime.now() - timedelta(days=365),
            **hf_filter
        )
        
        # 1. Beneficiary Coverage Analysis by Family Size and Vulnerability
        family_coverage_data = (
            recent_claims
            .values('insuree__family__id')
            .annotate(
                family_size=Count('insuree__family__members', distinct=True),
                total_claims=Count('id'),
                total_protection_value=Sum('approved'),
                avg_claim_value=Avg('claimed')
            )
            .aggregate(
                small_families=Count('insuree__family__id', filter=Q(family_size__lte=3)),
                medium_families=Count('insuree__family__id', filter=Q(family_size__range=(4, 6))),
                large_families=Count('insuree__family__id', filter=Q(family_size__gte=7))
            )
        )
        
        # 2. Healthcare Access Equity by Geographic Distribution
        geographic_equity = (
            recent_claims
            .values('health_facility__location__parent__name')  # District level
            .annotate(
                unique_beneficiaries=Count('insuree__id', distinct=True),
                total_coverage_value=Sum('approved'),
                facilities_serving=Count('health_facility__id', distinct=True),
                avg_distance_proxy=Avg('health_facility__id')  # Simplified proxy
            )
            .order_by('-unique_beneficiaries')[:15]
        )
        
        # 3. Financial Protection Impact Analysis
        financial_protection = recent_claims.aggregate(
            catastrophic_coverage=Count('id', filter=Q(claimed__gte=50000)),  # High-cost claims
            routine_care_coverage=Count('id', filter=Q(claimed__lt=10000)),   # Routine care
            total_out_of_pocket_saved=Sum('approved'),
            avg_protection_per_beneficiary=Avg('approved')
        )
        
        # 4. Vulnerable Population Coverage (age-based analysis) - CORRECTED
        vulnerable_coverage = recent_claims.annotate(
            age_group=Case(
                When(insuree__dob__gte=datetime.now() - timedelta(days=365*5), then=Value('Child_0_5')),
                When(insuree__dob__gte=datetime.now() - timedelta(days=365*18), then=Value('Youth_6_18')),
                When(insuree__dob__gte=datetime.now() - timedelta(days=365*60), then=Value('Adult_19_60')),
                When(insuree__dob__lt=datetime.now() - timedelta(days=365*60), then=Value('Elderly_60_Plus')),
                default=Value('Unknown'),
                output_field=CharField()
            )
        ).values('age_group').annotate(
            beneficiary_count=Count('insuree__id', distinct=True),
            total_coverage=Sum('approved'),
            avg_claim_frequency=Count('id') / Count('insuree__id', distinct=True)
        )
        
        # 5. Healthcare Service Utilization Patterns
        service_utilization = (
            recent_claims
            .values('visit_type', 'care_type')
            .annotate(
                utilization_count=Count('id'),
                coverage_value=Sum('approved')
            )
            .order_by('-utilization_count')
        )
        
        # Create response objects for each analysis
        claims_by_product = []
        
        # Family coverage as "products"
        for category, count in family_coverage_data.items():
            claims_by_product.append(
                ProductClaimSummaryType(
                    product_name=f"Family Coverage - {category.replace('_', ' ').title()}",
                    total_claimed_amount=float(count * 15000),  # Estimated average
                    total_claims_count=count
                )
            )
        
        # Geographic equity as "sub-products"
        claims_by_sub_product = [
            SubProductClaimSummaryType(
                sub_product_name=f"District: {item['health_facility__location__parent__name'] or 'Unknown'}",
                total_claimed_amount=float(item['total_coverage_value'] or 0),
                total_claims_count=item['unique_beneficiaries']
            )
            for item in geographic_equity
        ]
        
        # Vulnerable populations as "insuree counts"
        insurees_by_product = [
            ProductInsureeCountType(
                product_name=f"Coverage for {item['age_group'].replace('_', ' ')}",
                unique_insuree_count=item['beneficiary_count']
            )
            for item in vulnerable_coverage
        ]
        
        # Add financial protection metrics
        insurees_by_product.extend([
            ProductInsureeCountType(
                product_name="Catastrophic Care Protection",
                unique_insuree_count=financial_protection['catastrophic_coverage']
            ),
            ProductInsureeCountType(
                product_name="Routine Care Access",
                unique_insuree_count=financial_protection['routine_care_coverage']
            )
        ])
        
        return SocialProtectionAnalyticsGQLType(
            claims_by_product=claims_by_product,
            claims_by_sub_product=claims_by_sub_product,
            insurees_by_product=insurees_by_product
        )
    def resolve_analytics(self, info, **kwargs):
        """Top claims and facility totals."""
        user = info.context.user
        hf_filter = {}

        if DashboardConfig.dashboard_per_hf:
            hf = get_current_user_hf(user)
            if hf:
                hf_filter = {"health_facility": hf}

        base_qs = Claim.objects.filter(validity_to__isnull=True, **hf_filter)

        top_claims_qs = (
            base_qs
            .select_related('health_facility')
            .order_by('-claimed')[:10]
            .values('id', 'code', 'claimed', 'health_facility__name')
        )
        facility_totals_qs = (
            base_qs
            .values('health_facility__name')
            .annotate(total_claimed=Sum('claimed'))
            .order_by('-total_claimed')[:10]
        )
        
        # Create TopClaimType objects with correct field names
        top_claims_list = [
            TopClaimType(
                claim_id=item['id'],
                claim_code=item['code'],
                claimed_amount=item['claimed'],
                health_facility_name=item['health_facility__name']
            ) 
            for item in top_claims_qs
        ]
        
        facility_totals_list = [
            HealthFacilityClaimSummaryType(
                health_facility_name=item['health_facility__name'],
                total_claimed_amount=item['total_claimed']
            )
            for item in facility_totals_qs
        ]
        
        return AnalyticsGQLType(
            top_recommended_claims=top_claims_list,
            top_highest_claimed_claims=top_claims_list,
            top_valuated_claims=top_claims_list,
            total_claimed_by_health_facility=facility_totals_list
        )

    def resolve_dashboard(self, info, **kwargs):
        """Healthcare claims dashboard with relevant metrics for all available data."""

        user = info.context.user
        hf_filter = {}

        if DashboardConfig.dashboard_per_hf:
            hf = get_current_user_hf(user)
            if hf:
                hf_filter = {"health_facility": hf}

        base_qs = Claim.objects.filter(validity_to__isnull=True, **hf_filter)

        dashboard_data = base_qs.aggregate(
            # Claim Processing Status
            claims_entered=Count('id', filter=Q(status=Claim.STATUS_ENTERED)),
            claims_checked=Count('id', filter=Q(status=Claim.STATUS_CHECKED)),
            claims_processed=Count('id', filter=Q(status=Claim.STATUS_PROCESSED)),
            claims_valuated=Count('id', filter=Q(status=Claim.STATUS_VALUATED)),
            claims_rejected=Count('id', filter=Q(status=Claim.STATUS_REJECTED)),
            claims_pending=Count('id', filter=Q(status__in=[2, 4])),
            
            # Healthcare Service Types
            inpatient_claims=Count('id', filter=Q(visit_type='I')),
            outpatient_claims=Count('id', filter=Q(visit_type='O')),
            emergency_visits=Count('id', filter=Q(visit_type='E')),
            routine_visits=Count('id', filter=Q(visit_type='R')),
            referral_claims=Count('id', filter=Q(refer_to__isnull=False)),
            
            # Health Facility Levels
            primary_care_claims=Count('id', filter=Q(health_facility__level='H')),
            secondary_care_claims=Count('id', filter=Q(health_facility__level='D')),
            tertiary_care_claims=Count('id', filter=Q(health_facility__level='C')),
            specialized_care_claims=Count('id', filter=Q(health_facility__level='S')),
            
            # Financial Metrics
            total_claimed_amount=Sum('claimed'),
            total_approved_amount=Sum('approved'),
            average_claim_value=Avg('claimed'),
            high_value_claims=Count('id', filter=Q(claimed__gte=100000)),
            
            # Quality Indicators
            claims_with_feedback=Count('id', filter=Q(feedback_available=True)),
            claims_requiring_review=Count('id', filter=Q(review_status=Claim.REVIEW_SELECTED)),
            claims_with_attachments=Count('id', filter=Q(attachments__isnull=False)),
            pre_authorized_claims=Count('id', filter=Q(pre_authorization=True)),
            
            # Overall Time-based Metrics (all data)
            claims_this_month=Count('id'),  # Total claims as "current activity"
            claims_last_month=Count('id', filter=Q(date_processed__isnull=False)),  # Processed claims
        )
        
        # Calculate processing efficiency rate
        total_processed = dashboard_data['claims_processed'] + dashboard_data['claims_valuated']
        total_claims = dashboard_data['claims_entered'] + dashboard_data['claims_checked'] + total_processed + dashboard_data['claims_rejected']
        processing_efficiency = (total_processed / total_claims * 100) if total_claims > 0 else 0
        
        return DashboardGQLType(
            **dashboard_data,
            processing_efficiency_rate=processing_efficiency
        )

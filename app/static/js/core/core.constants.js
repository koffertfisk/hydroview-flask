(function() {
    'use strict';
    
    angular
        .module('app.core')
        .constant('DatePickerOptions', getDatePickerOptions())
        .constant('GoogleMapClusterOptions', getGoogleMapClusterOptions())
        .constant('GoogleMapDefaultOptions', getDefaultMapOptions())
        .constant('GoogleMapIcons', getGoogleMapIcons())
        .constant('HighChartOptions', getHighChartOptions());

    function getDatePickerOptions() {
        return {
            applyClass: 'btn-success',
            locale: {
                applyLabel: "Apply",
                fromLabel: "From",
                format: "YYYY-MM-DD HH:mm:ss",
                toLabel: "To",
                cancelLabel: 'Cancel',
                customRangeLabel: 'Custom Range'
            },
            ranges: {
                'Today': [moment(), moment()],
                'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                'This Month': [moment().startOf('month'), moment().endOf('month')],
                'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')],
                'Last 365 Days': [moment().subtract(364, 'days'), moment()]
            }
        };
    }
    
    function getGoogleMapClusterOptions() {
        return {
            imagePath: '/static/images/google-maps/cluster/m'
        };
    }
    
    function getDefaultMapOptions() {
        return {
            scrollwheel: false, 
            mapTypeControl: true, 
            streetViewControl: false, 
            mapTypeControlOptions: {
                mapTypeIds: ['roadmap', 'satellite', 'hybrid', 'terrain', 'styled_map'],
                style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
                position: google.maps.ControlPosition.TOP_CENTER
            },
            styles: [
                {
                    "featureType": "administrative",
                    "elementType": "labels.text.fill",
                    "stylers": [
                        {
                            "color": "#444444"
                        }
                    ]
                },
                {
                    "featureType": "landscape",
                    "elementType": "all",
                    "stylers": [
                        {
                            "color": "#f2f2f2"
                        }
                    ]
                },
                {
                    "featureType": "poi",
                    "elementType": "all",
                    "stylers": [
                        {
                            "visibility": "off"
                        }
                    ]
                },
                {
                    "featureType": "road",
                    "elementType": "all",
                    "stylers": [
                        {
                            "saturation": -100
                        },
                        {
                            "lightness": 45
                        }
                    ]
                },
                {
                    "featureType": "road.highway",
                    "elementType": "all",
                    "stylers": [
                        {
                            "visibility": "simplified"
                        }
                    ]
                },
                {
                    "featureType": "road.arterial",
                    "elementType": "labels.icon",
                    "stylers": [
                        {
                            "visibility": "off"
                        }
                    ]
                },
                {
                    "featureType": "transit",
                    "elementType": "all",
                    "stylers": [
                        {
                            "visibility": "off"
                        }
                    ]
                },
                {
                    "featureType": "water",
                    "elementType": "all",
                    "stylers": [
                        {
                            "color": "#46bcec"
                        },
                        {
                            "visibility": "on"
                        }
                    ]
                }
            ]
        };
    }
    
    function getGoogleMapIcons() {
        return {
            blueicon: '/static/images/google-maps/icons/blue-dot.png',
            greenicon: '/static/images/google-maps/icons/green-dot.png',
            redicon: '/static/images/google-maps/icons/red-dot.png'
        };
    }
    
    function getHighChartOptions() {
        return {
            title: {
                text: ''
            },
            subtitle: {
                text: ''
            },
            chart: {
                type: 'spline'
            },
            xAxis: {
                type: 'datetime',
                title: {
                    text: 'Time'
                }
            },
            yAxis: {
                title: {
                    text: ''
                },
                plotLines: [{
                    value: 0,
                    width: 1,
                    color: '#808080'
                }]
            },
            legend: {
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'middle',
                borderWidth: 0
            },
            plotOptions: {
                spline: {
                    marker: {
                        enabled: true
                    },
                }
            },
            tooltip: {
                pointFormat: '<span style="color:{point.color}">\u25CF</span> {series.name}: <b>{point.y:.2f} ' + '' + '</b><br/>',
                shared: true
            },
            series: [],
        };
    }

})();
(function() {
    'use strict';
    
    angular
        .module('app.location')
        .controller('LocationDataChartsGroupCtrl', LocationDataChartsGroupCtrl);
    
    LocationDataChartsGroupCtrl.$inject = [
        '$scope',
        'LocationParametersFactory',
        'locationMeasurements',
        'locationStorage',
        'locationDataSource', 
        'locationDataTimeOptions', 
        'HighChartOptions'
    ];
    
    function LocationDataChartsGroupCtrl($scope, LocationParametersFactory, locationMeasurements, locationStorage, locationDataSource, locationDataTimeOptions, HighChartOptions) {
        var vm = this;
        
        vm.chartParameter = {
            charts: {},
            group: {}
        };
        vm.getDailyStationsAverageChartData = getDailyStationsAverageChartData;
        vm.getHighFrequencyStationsAverageChartData = getHighFrequencyStationsAverageChartData;
        vm.getHourlyStationsAverageChartData = getHourlyStationsAverageChartData;
        vm.initChart = initChart;
        vm.initChartParameter = initChartParameter;
        vm.location = locationStorage.getLocation();
        vm.setChartSubtitle = setChartSubtitle;
        vm.setChartTitle = setChartTitle;
        vm.setDatePicker = setDatePicker;
        vm.setSelectedTimeOption = setSelectedTimeOption;
        vm.updateChartData = updateChartData;
        vm.updateDailyStationsAverageChartData = updateDailyStationsAverageChartData;
        vm.updateHighFrequencyStationsAverageChartData = updateHighFrequencyStationsAverageChartData;
        vm.updateHourlyStationsAverageChartData = updateHourlyStationsAverageChartData;
        
        vm.dataSourcesModel = {
            dataSources: locationDataSource.getDataSources(),
            selectedDataSource: locationDataSource.getSelectedDataSource()
        };
        
        vm.selectedTimeOption = null;
        
        vm.datePickerModel = {
            startDate: null,
            endDate: null
        }
        
        vm.setSelectedTimeOption();
        vm.setDatePicker();
        
        //function getDailyStationsAverageChartData(locationId, parameterId, qcLevel, fromDate, toDate) {
        //    return locationMeasurements.getDailyStationsChartAverageParameterMeasurements(locationId, parameterId, 0, fromDate, toDate)
        //        .then(function(response) {
        //            return response.data;
        //        });
        // }
        
        function getDailyStationsAverageChartData() {
            var locationId = vm.location.location_id;
            var groupId = vm.chartParameter.group.parameter_id;
            var fromDate = vm.datePickerModel.startDate.valueOf();
            var toDate = vm.datePickerModel.endDate.valueOf();
            return locationMeasurements.getDailyStationsChartAverageParameterGroupMeasurements(locationId, groupId, 0, fromDate, toDate)
                .then(function(response) {
                    return response.data;
                });
        }
        
        function getHighFrequencyStationsAverageChartData() {
            var locationId = vm.location.location_id;
            var groupId = vm.chartParameter.group.parameter_id;
            var fromDate = vm.datePickerModel.startDate.valueOf();
            var toDate = vm.datePickerModel.endDate.valueOf();
            return locationMeasurements.getHighFrequencyStationsChartAverageParameterGroupMeasurements(locationId, groupId, 0, fromDate, toDate)
                .then(function(response) {
                    return response.data;
                });
        }
        
        function getHourlyStationsAverageChartData() {
            var locationId = vm.location.location_id;
            var groupId = vm.chartParameter.group.parameter_id;
            var fromDate = vm.datePickerModel.startDate.valueOf();
            var toDate = vm.datePickerModel.endDate.valueOf();
            return locationMeasurements.getHourlyStationsChartAverageParameterGroupMeasurements(locationId, groupId, 0, fromDate, toDate)
                .then(function(response) {
                    return response.data;
                });
        }
        
        function initChartParameter(group) {
            vm.chartParameter.group = group;
            vm.chartParameter.charts.stationsAverageChart = angular.copy(HighChartOptions);
        }
        
        function initChart(chart) {
            vm.setChartSubtitle(chart);
            vm.setChartTitle(chart);
            vm.chartParameter.charts[chart].chart.zoomType = 'x';
            vm.chartParameter.charts[chart].yAxis.title.text = vm.chartParameter.group.parameter_name + ' (' + vm.chartParameter.group.parameter_unit + ')';
            vm.updateChartData();
        }
        
        function setChartTitle(chart) {
            var selectedDataSource = vm.dataSourcesModel.selectedDataSource;
            var groupName = vm.chartParameter.group.parameter_name;
            var locationName = vm.location.location_name;
            vm.chartParameter.charts[chart].title.text = selectedDataSource + ' Average ' + groupName + ' at ' + locationName;
        }
        
        function setChartSubtitle(chart) {
            var fromDate = vm.datePickerModel.startDate.format('YYYY-MM-DD HH:mm:ss');
            var toDate = vm.datePickerModel.endDate.format('YYYY-MM-DD HH:mm:ss');
            vm.chartParameter.charts[chart].subtitle.text = fromDate + ' - ' + toDate;
        }
        
        function setDatePicker() {
            vm.datePickerModel.startDate = locationDataTimeOptions.getTimeOptionDate(vm.selectedTimeOption)[0];
            vm.datePickerModel.endDate = locationDataTimeOptions.getTimeOptionDate(vm.selectedTimeOption)[1];
        }
        
        function setSelectedTimeOption() {
            vm.selectedTimeOption = locationDataTimeOptions.getSelectedTimeOption();
        }
        
        function updateChartData() {
            if (vm.dataSourcesModel.selectedDataSource === 'Daily') {
                vm.updateDailyStationsAverageChartData();
            }
            else if (vm.dataSourcesModel.selectedDataSource === 'Hourly') {
                vm.updateHourlyStationsAverageChartData();
            }
            else if (vm.dataSourcesModel.selectedDataSource === 'High Frequency') {
                vm.updateHighFrequencyStationsAverageChartData();
            }

        }
        
        function updateDailyStationsAverageChartData() {
            
            var parameterUnit = vm.chartParameter.group.parameter_unit;
            vm.chartParameter.charts.stationsAverageChart.series = [];
            vm.setChartTitle('stationsAverageChart');
            vm.setChartSubtitle('stationsAverageChart');
            vm.getDailyStationsAverageChartData().then(function(data) {
                for (var i = 0; i < data.length; i++) {
                    var series = data[i];
                    series.tooltip = {
                        'headerFormat': '<span style="font-size: 10px">{point.key: %Y-%m-%d %H:%M:%S}</span><br/>',
                        'pointFormat': '<span style="color:{point.color}">\u25CF</span> {series.name}: <b>{point.y:.2f} ' + parameterUnit + '</b><br/>'
                    };
                    vm.chartParameter.charts.stationsAverageChart.series.push(series);
                }
            });
        }
        
        function updateHighFrequencyStationsAverageChartData() {
            var parameterUnit = vm.chartParameter.group.parameter_unit;
            vm.chartParameter.charts.stationsAverageChart.series = [];
            vm.setChartTitle('stationsAverageChart');
            vm.setChartSubtitle('stationsAverageChart');
            vm.getHighFrequencyStationsAverageChartData().then(function(data) {
                for (var i = 0; i < data.length; i++) {
                    var series = data[i];
                    series.tooltip = {
                        'headerFormat': '<span style="font-size: 10px">{point.key: %Y-%m-%d %H:%M:%S}</span><br/>',
                        'pointFormat': '<span style="color:{point.color}">\u25CF</span> {series.name}: <b>{point.y:.2f} ' + parameterUnit + '</b><br/>'
                    };
                    vm.chartParameter.charts.stationsAverageChart.series.push(series);
                }
            });
        }
        
        function updateHourlyStationsAverageChartData() {
            var parameterUnit = vm.chartParameter.group.parameter_unit;
            vm.chartParameter.charts.stationsAverageChart.series = [];
            vm.setChartTitle('stationsAverageChart');
            vm.setChartSubtitle('stationsAverageChart');
            vm.getHourlyStationsAverageChartData().then(function(data) {
                for (var i = 0; i < data.length; i++) {
                    var series = data[i];
                    series.tooltip = {
                        'headerFormat': '<span style="font-size: 10px">{point.key: %Y-%m-%d %H:%M:%S}</span><br/>',
                        'pointFormat': '<span style="color:{point.color}">\u25CF</span> {series.name}: <b>{point.y:.2f} ' + parameterUnit + '</b><br/>'
                    };
                    vm.chartParameter.charts.stationsAverageChart.series.push(series);
                }
            });
        }
        
        $scope.$on('dataSourceChange', function() {
            vm.dataSourcesModel.selectedDataSource = locationDataSource.getSelectedDataSource();
            vm.updateChartData();
        });
        
        $scope.$on('datePickerChange', function() {
            vm.setSelectedTimeOption();
            vm.setDatePicker();
            vm.updateChartData();
        });
        
    }
    
})();
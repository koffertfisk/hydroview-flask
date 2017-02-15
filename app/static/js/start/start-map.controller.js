(function() {
    'use strict';
    
    angular
        .module('app.start')
        .controller('StartMap', StartMap);
    
    function StartMap(LocationsFactory, GoogleMapDefaultOptions) {
        var vm = this;
        
        vm.addLocationMarkers = addLocationMarkers;
        vm.addStationMarkers = addStationMarkers;
        vm.markers = [];
        vm.locations = [];
        vm.map = { center: { latitude: 63, longitude: 16}, zoom: 12 };
        vm.mapOptions = GoogleMapDefaultOptions;
        vm.icons = {
            blueicon: '/static/images/google-maps/icons/blue-dot.png',
            greenicon: '/static/images/google-maps/icons/green-dot.png',
            redicon: '/static/images/google-maps/icons/red-dot.png'
        };
        
        vm.clusterOptions = {
            imagePath: '/static/images/google-maps/cluster/m'
        };
        
        activate();

        function addLocationMarkers(locations) {
            var markers = [];
            for (var i = 0; i < locations.length; i++) {
                markers.push({
                    latitude: locations[i].position.latitude,
                    longitude: locations[i].position.longitude,
                    icon: vm.icons.redicon,
                    key: 'marker-id-' + locations[i].id,
                    options: {
                        title: locations[i].name,
                    }
                });
                
                markers = addStationMarkers(locations[i].location_stations, markers);

            }
            
            return markers;
        }
        
        function addStationMarkers(stations, markers) {
            for (var i = 0; i < stations.length; i++) {
                markers.push({
                    latitude: stations[i].station_position.latitude,
                    longitude: stations[i].station_position.longitude,
                    icon: vm.icons.blueicon,
                    key: 'marker-id-' + stations[i].station_id,
                    options: {
                        title: stations[i].station_name,
                    }
                });
            }
            
            return markers;
            
        }
        
        function activate() {
            return getLocations().then(function() {
                vm.markers = addLocationMarkers(vm.locations);
            });
        }
        
        function getLocations() {
            return LocationsFactory.getLocations()
                .then(function(response) {
                    vm.locations = response.data;
                    return vm.locations;
                });
        }
        
    }

})();

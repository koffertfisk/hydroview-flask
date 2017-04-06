(function() {    
    'use strict';
    
    angular
        .module('app.services')
        .factory('locationParameters', locationParameters);
    
    locationParameters.$inject = ['$resource'];
    
    function locationParameters($resource) {

        var customInterceptor = {
            response: function(response) {
                return response;
            }
        };
        
        return {
            getParameterMeasurementTypes: getParameterMeasurementTypes
        };
        
        function getParameterMeasurementTypes(locationId) {
            var resource = $resource('/api/parameter_measurement_types_by_location/:location_id', {}, {
                query: {
                    method: 'GET', params: {
                        location_id: locationId, 
                    },
                    isArray: true,
                    interceptor: customInterceptor
                }
            });
            
            return resource.query({location_id: locationId}).$promise
                .then(getParameterMeasurementTypesComplete)
                .catch(getParameterMeasurementTypesFailed);
                
            function getParameterMeasurementTypesComplete(response) {
                return response;
            }
            
            function getParameterMeasurementTypesFailed(error) {
                console.log(error);
            }

        }
        
    }

})();

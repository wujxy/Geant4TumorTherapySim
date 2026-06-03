cmake_minimum_required(VERSION 3.16)
project(Geant4TumorTherapySim LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Geant4 REQUIRED ui_all vis_all)

include(${Geant4_USE_FILE})
include_directories(${PROJECT_SOURCE_DIR}/include)

file(GLOB sources CONFIGURE_DEPENDS ${PROJECT_SOURCE_DIR}/src/*.cc)
file(GLOB headers CONFIGURE_DEPENDS ${PROJECT_SOURCE_DIR}/include/*.hh)

add_executable(tumor_therapy main.cc ${sources} ${headers})
target_link_libraries(tumor_therapy ${Geant4_LIBRARIES})

install(TARGETS tumor_therapy DESTINATION bin)

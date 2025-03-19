#
# Copyright (C) 2022-2025 Intel Corporation
#
# SPDX-License-Identifier: MIT
#

if (NOT BUILD_SYCL_ACPP)
    add_benchmark(graph_api_benchmark sycl l0 ur all)
endif()

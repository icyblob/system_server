#include "node_utils_wrapper.h"

#include <nodeUtils.h>
#include <iostream>

int getTickNumberFromNode(const char* nodeIp, const int nodePort, uint32_t& currentTickNumber)
{
    currentTickNumber = 0;
    QCPtr qc;
    try
    {
        qc = make_qc(nodeIp, nodePort);
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return 1;
    }
    
    try
    {
        currentTickNumber = getTickNumberFromNode(qc);
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return 1;
    }

    return 0;
}
#include <h5cpp/hdf5.hpp>
#include <iostream>
#include <unistd.h>


int main()
{

  hdf5::property::FileAccessList fapl;
  hdf5::property::FileCreationList fcpl;

  auto file = hdf5::file::create(
				"piltest_11416.nxs",
                                hdf5::file::AccessFlags::SWMR_WRITE |
                                hdf5::file::AccessFlags::TRUNCATE, fcpl, fapl);
  auto root = file.root();

  hdf5::property::DatasetCreationList dcpl;
  dcpl.layout(hdf5::property::DatasetLayout::CHUNKED);
  dcpl.chunk({1, 3, 2});
  hdf5::Dimensions s = {0, 3, 2};
  hdf5::Dimensions m = {hdf5::dataspace::Simple::UNLIMITED,
                        hdf5::dataspace::Simple::UNLIMITED,
                        hdf5::dataspace::Simple::UNLIMITED};
  hdf5::dataspace::Simple sp(s, m);
  hdf5::property::LinkCreationList lcpl;
  hdf5::property::DatasetAccessList dapl;
  hdf5::dataspace::Hyperslab framespace;
  framespace = hdf5::dataspace::Hyperslab({{0, 0, 0}, {1, 3, 2}});
  auto int_type = hdf5::datatype::create<int>();
  auto ds1 = hdf5::node::Dataset(root,
                                 hdf5::Path("data"),
                                 int_type,
                                 sp, lcpl, dcpl, dapl);

  std::vector<int> buffer = {1, 2, 3, 4, 5, 6};
  for(long long unsigned int  i=0; i!=50; i++){
    std::cout << i << std::endl;
    ds1.extent(0, 1);
    framespace.offset({i, 0, 0});
    for(auto& value: buffer)
      value ++;
    ds1.write(buffer, framespace);
    file.flush(hdf5::file::Scope::GLOBAL);
    usleep(1000 * 1000);
  }
  ds1.close();

  root.close();
  file.close();
  return 0;
}

